import os
import dotenv
import requests
import json
from datetime import datetime, timedelta, date
import pandas as pd
import time

tokens = ['TOKEN 1', 'TOKEN 2', 'TOKEN 3', 'TOKEN 4']
current_token_index = 0

def get_current_token():
    global current_token_index
    return tokens[current_token_index]

def switch_token():
    global current_token_index
    current_token_index = (current_token_index + 1) % len(tokens)



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


def calculate_pr_interval(created_at, merged_at, closed_at): 
  if merged_at:
      end_time = datetime.strptime(merged_at, "%Y-%m-%dT%H:%M:%SZ")
  else:
      end_time = datetime.strptime(closed_at, "%Y-%m-%dT%H:%M:%SZ")

  start_time = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
  age = end_time - start_time

  return age.total_seconds() / 3600


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
              stargazerCount
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
              comments {
                  totalCount
              }
              number
              title
              reviews(first: 1) {
                totalCount
              }
              mergedAt
              closedAt
              createdAt
              bodyText
              participants(first: 50) {
              nodes {
                  login
                }
              }
            }
          }
        }
      }
    }
    """ % (owner, repo_name)

    return run_query(query, headers)


def get_repository_commit_stats(owner, repo_name, headers):
    query = """
    {
      repository(owner: "%s", name: "%s") {
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 50) {
                edges {
                  node {
                    additions
                    deletions
                  }
                }
              }
            }
          }
        }
      }
    }
    """ % (owner, repo_name)

    return run_query(query, headers)


def get_repository_files(owner, repo_name, headers):
    query = """
    {
      repository(owner: "%s", name: "%s") {
        object(expression: "HEAD:") {
          ... on Tree {
            entries {
              name
            }
          }
        }
      }
    }
    """ % (owner, repo_name)

    return run_query(query, headers)


dotenv.load_dotenv()
headers = {"Authorization": "Bearer " + get_current_token()}

index = 1
repos = []
end_cursor = "null"
num_repos = 200
calls_counter = 0
while len(repos) < num_repos:
    try:
        calls_counter +=1

        if calls_counter > 20:
          switch_token()
          calls_counter = 0

        repositories_data = search_repositories(end_cursor, headers)['data']['search']

        if 'errors' in repositories_data:
          print("GraphQL query failed:", data['errors'])
          print("Waiting for 60 seconds before retrying...")
          time.sleep(60)
          continue

    except:
        continue

    end_cursor = "\"" + repositories_data["pageInfo"]["endCursor"] + "\"" if repositories_data["pageInfo"]["endCursor"] is not None else "null"
    time.sleep(1)
    
    repositories = []
    repositories.extend(list(map(lambda x: x['node'], repositories_data['edges'])))

    for repo in repositories:
      
      total_reviews_pr = 0
      repo_name_with_owner = repo['nameWithOwner']
      count_pr_repo = repo['pullRequests']['totalCount']

      attempts = 0

      while attempts < 8:
        try:
          pull_requests = get_pull_requests(*repo_name_with_owner.split('/'), headers)['data']['repository']['pullRequests']['nodes']
          switch_token()
          time.sleep(1)
          break
        except Exception as ex:
          attempts += 1
          print(f"Waiting 60 seconds before retrying...")
          time.sleep(60)
        
      for pr in pull_requests:
        if int(pr['reviews']['totalCount']) > 0 and is_review_duration_greater_than_one_hour(pr['createdAt'], pr['mergedAt'], pr['closedAt']):
          total_reviews_pr += int(pr['reviews']['totalCount'])

      if (total_reviews_pr > 0 and is_review_duration_greater_than_one_hour(pr['createdAt'], pr['mergedAt'], pr['closedAt'])):

        grand_total_rows_added_and_removes = 0
        total_rows_added = 0
        total_rows_removed = 0
        getCommitStatsAttempt = 0

        while getCommitStatsAttempt < 8:
          try:
            for commit in get_repository_commit_stats(*repo_name_with_owner.split('/'), headers)['data']['repository']['defaultBranchRef']['target']['history']['edges']:
              total_rows_added += commit['node']['additions']
              total_rows_removed += commit['node']['deletions']
              grand_total_rows_added_and_removes += total_rows_added + total_rows_removed
            switch_token()
            time.sleep(1)
            break
          except Exception as ex:
            getCommitStatsAttempt += 1
            print(f"Waiting 60 seconds before retrying to get commit stats...")
            time.sleep(60)

        total_repository_files = get_repository_files(*repo_name_with_owner.split('/'), headers)['data']['repository']['object']['entries']
        # print(json.dumps(pull_requests[index - 1], indent=3))
        repos.append({
          'repo_name_with_owner': repo['nameWithOwner'],
          'stars': repo['stargazerCount'],
          'total_pr': repo['pullRequests']['totalCount'],
          'total_pr_reviews': total_reviews_pr,
          'total_repository_files': len(total_repository_files),
          'analysis_time': calculate_pr_interval(pr['createdAt'], pr['mergedAt'], pr['closedAt']),
          'number_characters_description': len(list(pr['bodyText'])),
          'number_participants': len(pr['participants']['nodes']),
          'total_comments_pr': pr['comments']['totalCount'],
          'total_rows_added': total_rows_added,
          'total_rows_removed': total_rows_removed,
          'grand_total_rows_added_and_removed': grand_total_rows_added_and_removes,
          'index': index
        })
        switch_token()
        time.sleep(1)

        index +=1

print(json.dumps(repos, indent=1))

df = pd.DataFrame(data=repos)

if not os.path.exists('./dataset'):
  os.mkdir('./dataset')

df.to_csv('./dataset/repos.csv', index=False)

print('Finished')