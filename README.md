# github_api_licensing
This project allows you to detect unlicensed repositories in a Github organization. It then creates a pull request to add an Apache License 2.0 as the project license. 


Assumptions:
You should be running Python 3+.
You should have the Python Requests package available when you run the script. http://docs.python-requests.org/en/master/ 
You will need to enter the organization name, email and a personal access token. You can generate a token at: https://github.com/settings/tokens 

Running:
Simply clone the repo, then run the script in your terminal of choice. 
```
py licensing.py
```


