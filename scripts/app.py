import os
import dotenv
import requests
import json
from datetime import datetime, timedelta, date
import pandas as pd


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
              pullRequests(states: [MERGED, CLOSED], first: 50) {
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
        pullRequests(states: [MERGED, CLOSED], first: 5) {
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
headers = {"Authorization": "Bearer " + os.environ['API_TOKEN']}

index = 1
repos = []
end_cursor = "null"
num_repos = 50
while len(repos) < num_repos:
    try:
        repositories_data = search_repositories(end_cursor, headers)['data']['search']
    except:
        continue

    end_cursor = "\"" + repositories_data["pageInfo"]["endCursor"] + "\"" if repositories_data["pageInfo"]["endCursor"] is not None else "null"
    repositories = []
    repositories.extend(list(map(lambda x: x['node'], repositories_data['edges'])))

    for repo in repositories:
      total_reviews_pr = 0
      repo_name_with_owner = repo['nameWithOwner']
      count_pr_repo = repo['pullRequests']['totalCount']

      pull_requests = get_pull_requests(*repo_name_with_owner.split('/'), headers)['data']['repository']['pullRequests']['nodes']

      for pr in pull_requests:
        if int(pr['reviews']['totalCount']) > 0 and is_review_duration_greater_than_one_hour(pr['createdAt'], pr['mergedAt'], pr['closedAt']):
          total_reviews_pr += int(pr['reviews']['totalCount'])

      if total_reviews_pr > 0:

        grand_total_rows_added_and_removes = 0
        total_rows_added = 0
        total_rows_removed = 0

        for commit in get_repository_commit_stats(*repo_name_with_owner.split('/'), headers)['data']['repository']['defaultBranchRef']['target']['history']['edges']:
          total_rows_added += commit['node']['additions']
          total_rows_removed += commit['node']['deletions']
          grand_total_rows_added_and_removes += total_rows_added + total_rows_removed

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
        index +=1

print(json.dumps(repos, indent=1))

df = pd.DataFrame(data=repos)

if not os.path.exists('./dataset'):
  os.mkdir('./dataset')

df.to_csv('./scripts/dataset/repos.csv', index=False)

print('Finished')