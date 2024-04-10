import os
import dotenv
import requests
import json
from datetime import datetime, timedelta

def run_query(query, headers):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, request.text))
    

def is_review_duration_greater_than_one_hour(review_created_at, pr_merged_at, pr_closed_at):
    review_created_at = datetime.strptime(review_created_at, '%Y-%m-%dT%H:%M:%SZ')
    pr_merged_at = datetime.strptime(pr_merged_at, '%Y-%m-%dT%H:%M:%SZ') if pr_merged_at else None
    pr_closed_at = datetime.strptime(pr_closed_at, '%Y-%m-%dT%H:%M:%SZ') if pr_closed_at else None
    
    if pr_merged_at:
        time_difference = pr_merged_at - review_created_at
    elif pr_closed_at:
        time_difference = pr_closed_at - review_created_at
    else:
        return False
    
    return time_difference > timedelta(hours=1)



def search_repositories(end_cursor, headers):
    query = """
    {
      search(
        query: "stars:>20000"
        type: REPOSITORY
        first: 1
        after: """ + end_cursor + """
      )
      {
        pageInfo {
        endCursor
        hasNextPage
        } 
        edges {
          node {
            ... on Repository {
              nameWithOwner
              pullRequests(states: [MERGED, CLOSED], first: 100) {
                totalCount
              }
            }
          }
        }
      }
    }
    """

    return run_query(query, headers)


def get_pull_requests(owner, repo_name, headers):
    query = """
    {
      repository(owner: "%s", name: "%s") {
        pullRequests(states: [MERGED, CLOSED], first: 100) {
          nodes {
            ... on PullRequest {
              number
              title
              reviews(first: 1) {
                totalCount              
              }
              mergedAt
              closedAt
              createdAt
            }
          }
        }
      }
    }
    """ % (owner, repo_name)

    return run_query(query, headers)

if __name__ == "__main__":
    index = 1
    data = []
    end_cursor = "null"
    num_repos = 200
    while len(data) < num_repos:
        dotenv.load_dotenv()
        headers = {"Authorization": "Bearer " + os.environ['API_TOKEN']}

        try:
            repositories_data = search_repositories(end_cursor, headers)['data']['search']
        except:
            continue

        end_cursor = "\"" + repositories_data["pageInfo"]["endCursor"] + "\"" if repositories_data["pageInfo"]["endCursor"] is not None else "null"
        repositories = []
        repositories.extend(list(map(lambda x: x['node'], repositories_data['edges'])))

        for repo_edge in repositories:
            repo_name_with_owner = repo_edge['nameWithOwner']
            
            pull_requests_data = get_pull_requests(*repo_name_with_owner.split('/'), headers)
            
            for pr_node in pull_requests_data['data']['repository']['pullRequests']['nodes']:                
                if int(pr_node['reviews']['totalCount']) > 0 and is_review_duration_greater_than_one_hour(pr_node['createdAt'], pr_node['mergedAt'], pr_node['closedAt']):
                    data.append({
                        'repo': repo_edge['nameWithOwner'],
                        # 'pr_number': pr_node['number'],
                        'pr_description': pr_node['title'],
                        'pr_reviews_count': pr_node['reviews']['totalCount'],
                        'index': index
                    })
                    index +=1
                
    print(json.dumps(data, indent=1))
