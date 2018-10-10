# Author: David Owen
# October 2018

import requests
import base64


def get_org_info(org_name, token):
    if org_name == "":
        print("No organization name passed in.")
        return

    if token == "":
        print("No token passed in.")
        return

    # Define starting parameters
    url = "https://api.github.com/orgs/" + org_name + "/repos"
    headers = {
        "Authorization": "token " + token
    }

    # API call: Get user data, name and email
    user_data = get_user_data(headers)

    if user_data is None:
        return

    while True:
        # API call: Get the Organizations repositories.
        org_response = requests.get(url, headers=headers)

        if org_response.status_code != 200:
            print("Error getting " + org_name)
            print("Status code: " + str(org_response.status_code))
            print(org_response.json())
            break

        # Grab each repo and see if there is a license assigned.
        for repo in org_response.json():
            repo_name = repo['name']

            if repo['license'] is None:
                print("No license found for " + repo_name)

                # API call: Get a git ref to the head of the master branch
                head_response = get_head_ref(headers, org_name, repo_name)
                if head_response is None:
                    continue

                # Extract sha value pointing to head from the response body
                sha = head_response.json()['object']['sha']

                # API call: Creates a new branch from the head of master
                branch_response = create_branch(sha, headers, org_name, repo_name)
                if branch_response is None:
                    continue

                # Extract new branch name from the response body
                branch_name = branch_response.json()['ref'].replace("refs/heads/", "")

                # API call: Creates the license file
                create_response = create_license(branch_name, headers, org_name, repo_name, user_data, sha)
                if create_response is None:
                    continue

                # API call: Creates a new pull request for the licensing branch
                pull_response = create_pull_request(branch_name, headers, repo)
                if pull_response is None:
                    continue

        # Handle pagination for large organizations
        # Checking for next page of repos
        if 'next' in org_response.links:
            print("Next page found")
            url = org_response.links['next']['url']
        else:
            # No additional pages so we are finished checking for licenses
            break


def get_head_ref(headers, org_name, repo_name):
    print("Getting reference to head")
    head_url = "https://api.github.com/repos/" + org_name + "/" + repo_name + "/git/refs/heads/master"
    head_response = requests.get(head_url, headers=headers)

    if head_response.status_code != 200:
        print("Status code: " + str(head_response.status_code))
        print(head_response.json())
        return None

    return head_response


def get_user_data(headers):
    user_url = "https://api.github.com/user"
    user_response = requests.get(user_url, headers=headers)

    if user_response.status_code != 200:
        print("Invalid token")
        print("Status code: " + str(user_response.status_code))
        print(user_response.json())
        return None

    user_data = user_response.json()
    if user_data['email'] is None:
        user_data['email'] = input("Please enter the email you use with github: ")

    return user_data


def create_pull_request(branch_name, headers, repo):
    print("Creating pull request")
    pull_url = "https://api.github.com/repos/" + repo['owner']['login'] + "/" + repo['name'] + "/pulls"
    json = {
        "title": "Add LICENSE file to repository",
        "body": "Please add a LICENSE file to your project. https://choosealicense.com/ is a resource with details"
                " on some of the common licenses available for github projects. I have create an Apache License 2.0 "
                "file for you but please review the other available options.",
        "head": branch_name,
        "base": "master"
    }
    pull_response = requests.post(pull_url, json=json, headers=headers)

    if pull_response.status_code != 201:
        print("Status code: " + str(pull_response.status_code))
        print(pull_response.json())
        return None

    return pull_response


def create_license(branch_name, headers, owner, repo_name, user_data, sha):
    print("Creating file")
    create_url = "https://api.github.com/repos/" + owner + "/" + repo_name + "/contents/LICENSE"
    with open('LICENSE', 'r') as license_file:
        license_data = license_file.read()
        license_encoded = base64.standard_b64encode(license_data.encode('UTF-8')).decode('ascii')
    json = {
        "message": "Adding LICENSE file",
        "branch": branch_name,
        "committer": {
            "name": user_data['name'],
            "email": user_data['email']
        },
        "content": license_encoded,
        "sha": sha
    }
    create_response = requests.put(create_url, json=json, headers=headers)

    if create_response.status_code != 201:
        print("Status code: " + str(create_response.status_code))
        print(create_response.json())
        return None

    return create_response


def create_branch(sha, headers, org_name, repo_name, branch_name="AddLicense"):
    print("Creating branch")
    post_url = "https://api.github.com/repos/" + org_name + "/" + repo_name + "/git/refs"
    json = {
        "ref": "refs/heads/" + branch_name,
        "sha": sha
    }
    branch_response = requests.post(post_url, json=json, headers=headers)

    # For handling name collision
    # Comment out this if block to ignore repos that already have the licensing branch created
    if branch_response.status_code == 422:
        # Duplicate branch name so add to the name and try again.
        branch_name = input("Branch named '" + branch_name + "' already exists. Enter 'skip' to ignore this repository"
                                                             " or enter a new name: ")
        if branch_name != "skip":
            return create_branch(sha, headers, org_name, repo_name, branch_name)
        else:
            return None

    # Handle other error codes
    if branch_response.status_code != 201:
        print("Status code: " + str(branch_response.status_code))
        print(branch_response.json())
        return None

    return branch_response


def main():
    while True:
        org_name = input("Enter your github organization name: ")
        token = input("Enter your personal access token: ")
        get_org_info(org_name, token)

        print("Finished checking " + org_name)
        next_org = input("Would you like to check another (O/o)rganization or (E/e)xit? ")
        if next_org == "E" or next_org == "e":
            break
        if next_org == "O" or next_org == "o":
            print("---------------------------------------------------------------------")
            continue
        else:
            print("Invalid input, exiting.")


main()
