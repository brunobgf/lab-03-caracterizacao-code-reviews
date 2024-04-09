import requests
import pandas as pd
from datetime import datetime
import os
import dotenv
import json
import os


def run_query(query, headers):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, request.text))


index = 1
data = []
end_cursor = "null"
num_repos = 200
while len(data) < num_repos:
  query = '''{
    search (
        query: "stars:>20000"
        type: REPOSITORY
        first: 2
        after: ''' + end_cursor + '''
      ) {
        pageInfo {
        endCursor
        hasNextPage
      }
      edges {
        node {
          ... on Repository {
            nameWithOwner
            stargazerCount
            url
            pullRequests(states: [CLOSED, MERGED]) {
              totalCount
            }
          }
        }
      }
    }
  }
  '''
  dotenv.load_dotenv()
  headers = {"Authorization": "Bearer " + os.environ['API_TOKEN']}

#   print(json.dumps(run_query(query, headers), indent=3))
#   input()

  result = run_query(query, headers)["data"]["search"]
  end_cursor = "\"" + result["pageInfo"]["endCursor"] + "\"" #if result["pageInfo"]["endCursor"] is not None else "null"
  repositories = []
  repositories.extend(list(map(lambda x: x['node'], result['edges'])))

  for repo in repositories:
      data.append({
          'name': repo['nameWithOwner'].split('/')[1],
          'owner': repo['nameWithOwner'].split('/')[0],
          'url': repo['url'],
          'stars': repo['stargazerCount'],
          'index': index
      })
      index += 1

print(json.dumps(data, indent=1))

# df = pd.DataFrame(data=data)

# if not os.path.exists('./output_repos'):
#   os.mkdir('./output_repos')

# # df.to_json('./output_repos/repos.json', index=False)
# df.to_csv('./scripts/output_repos/repos.csv', index=False)

print('Finished')
