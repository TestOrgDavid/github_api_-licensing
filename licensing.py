# Author: David Owen
# October 2018

# 1. Write code, in the language of your choice, that using the github API, goes through
#    all the public and private github repos in a github organization and checks if they have
#    a license.  (You can create a free github.com organization to test with here.)
# 2. Write code that if the license is missing, opens a pull request which adds a license.
#    (More info about licenses can be found here: https://choosealicense.com/)
# 3. Save your code (finished or not) into a public github repo.
# 4. Document any assumptions you made, instructions on how to run your code and anything 
#    else you want me to know using a README.md file in the root of the directory tree in the repo.
# 5. Reply to this email giving me the link to the repo with your code at or before 
#    Wednesday, October 10, 2018. If you don't finish all of the requirements on time please send
#    the link by the deadline anyway.

import requests
import base64


def get_org_info(org_name, token):

    if org_name == "":
        print("No organization name passed in.")
        return

    if token == "":
        print("No token passed in.")
        return

    url = "https://api.github.com/orgs/" + org_name + "/repos"
    headers = {
        'Authorization': 'token ' + token
    }

    while True:
        # Get the Organizations repositories.
        org_response = requests.get(url, headers=headers)

        if org_response.status_code != 200:
            print("Status code: " + str(org_response.status_code))
            print(org_response.json())
            break

        # Grab each repo and see if there is a license assigned.
        for repo in org_response.json():
            owner = repo['owner']['login']
            repo_name = repo['name']

            if repo['license'] is None:
                print("No license found for " + repo['name'])

                branch_name = "AddLicense"

                print("Getting reference to head")
                head_url = "https://api.github.com/repos/" + owner + "/" + repo_name + "/git/refs/heads/master"
                head_response = requests.get(head_url, headers=headers)

                branch_response = create_branch(branch_name, head_response, headers, repo)

                if branch_response.status_code != 201:
                    print("Status code: " + str(branch_response.status_code))
                    print(branch_response.json())
                    continue

                create_response = create_license(branch_name, headers, owner, repo_name)

                if create_response.status_code != 201:
                    print("Status code: " + str(create_response.status_code))
                    print(create_response.json())
                    continue

                pull_response = create_pull_request(branch_name, headers, repo)

                if pull_response.status_code != 201:
                    print("Status code: "+str(pull_response.status_code))
                    print(pull_response.json())
                    continue

        # Handle pagination for large organizations
        # Checking for next page of repos
        if 'next' in org_response.links:
            print("Next page found")
            url = org_response.links['next']['url']
        else:
            # No additional pages so we are finished checking for licenses
            break


def create_pull_request(branch_name, headers, repo):
    print("Creating pull request")
    pull_url = "https://api.github.com/repos/" + repo['owner']['login'] + "/" + repo['name'] + "/pulls"
    json = {
        "title": "Add LICENSE file to repository",
        "body": "Please pull the created license for your project or choose a different one from"
                " https://choosealicense.com/ . This site is a resource with details on some of the "
                "common licenses available for github projects. I have create an Apache License 2.0 "
                "file for you but please review the other available options.",
        "head": branch_name,
        "base": "master"
    }
    pull_response = requests.post(pull_url, json=json, headers=headers)
    return pull_response


def create_license(branch_name, headers, owner, repo_name):
    print("Creating file")
    create_url = "https://api.github.com/repos/" + owner + "/" + repo_name + "/contents/LICENSE"
    with open('LICENSE', 'r') as license_file:
        license_data = license_file.read()
        license_encoded = base64.standard_b64encode(license_data.encode('UTF-8')).decode('ascii')
    json = {
        "message": "Adding LICENSE file",
        "branch": branch_name,
        "committer": {
            "name": "David Owen",
            "email": "david.owen.dev@gmail.com"
        },
        "content": license_encoded
    }
    create_response = requests.put(create_url, json=json, headers=headers)
    return create_response


def create_branch(branch_name, head_response, headers, repo):
    print("Creating branch")
    sha = head_response.json()['object']['sha']
    post_url = "https://api.github.com/repos/" + repo['owner']['login'] + "/" + repo['name'] + "/git/refs"
    json = {
        "ref": "refs/heads/" + branch_name,
        "sha": sha
    }
    branch_response = requests.post(post_url, json=json, headers=headers)

    # For handling name collision
    # if branch_response.status_code == 422:
    #     # Duplicate branch name so add to the name and try again.
    #     branch_name += "-A"
    #     branch_response = create_branch(branch_name, head_response, headers, repo)

    return branch_response


def main():
    org_name = input("Enter your github organization name: ")
    token = input("Enter your personal access token: ")
    get_org_info(org_name, token)


main()