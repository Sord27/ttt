# Jira Comment Automation  

## This Jira class that allows for editing or modifying any comment in the Jira issue using python. Also, can upload attachment to the jira issue. 

## Requirements:

1- Install jira package
 
            Pip3 Install jira

2- Need to create a secret.json file to contain your jira’s account access and its token. Also, to contain your correct URL for your jira space.
```
    {
        "jira_url": "XXXXXXXXXXXXXXX",
        "jira_username": "XXXXXXXXXXXXXXX",
        "jira_token": "XXXXXXXXXXXXXXX"

    }
```
3- The jira issue you want work with, for example; "WOLK-580".

## How it works

In Jira issues comments are indexed from 0 to the last comment entered in the jira issue. But, we modified the python code to start from 1. 

A- Initialize your object; 

        TEST = JiraComment(JIRA_ISSUE)  forexample; TEST = JiraComment("WOLK-580")

B- Retrieve the ID for the comment you want to modify; 

        COMMENT_LIST = TEST.get_comment_id(5)
        get_comment_id() will return a tuple, the first index contain a true or false and the second index 
        contains the reason for the false return or the comment ID  you want to modify, respectively. 
        COMMENT_ID = COMMENT_LIST[1]
  
C- Get the content of the comment body to modify 

        COMMENT_BODY = TEST.get_comment_content(“WOLK-580”, COMMENT_ID)
        
D- After modifying the original comment’s content, you can update it back with;

        TEST.update_comment(“WOLK-580”, COMMENT_ID, MODIFIED_COMMENT)
        
E- Adding a new comment to the end of the list of the Jira issue; 

	    TEST.add_comment(WOLK-580”, NEW_COMMENT_TO_ADD)
	    
F- Adding attachment to the Jira issue: 

        TEST.attach_file(JIRA_ISSUE, FILE_PATH)


## How to run

    python3 jira_comment.py
    
    A main() method included with script as a test eaxmple to follow. 








