import os
import dotenv
import requests
import json

def run_query(query, headers):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, request.text))


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

# result = search_repositories('null')['data']['search']
# repositories = []
# repositories.extend(list(map(lambda x: x['node'], result['edges'])))
# print(json.dumps(repositories, indent=2))#repositories[0]["nameWithOwner"]
# print('Fim')
# input()


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
                print(json.dumps(pr_node, indent=3))
                input()
                # input()
                if int(pr_node['reviews']['totalCount']) > 0:
                    print('entrei')
                    data.append({
                        'pr_number': pr_node['number'],
                        'pr_title': pr_node['title'],
                        'pr_reviews_count': pr_node['reviews']['totalCount'],
                        'index': index
                    })
                    index +=1
                
    print(json.dumps(data, indent=1))
