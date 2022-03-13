"""This class will update, modify or add comment to existing Jira issue
Version = 1.0
"""
import json
import re
from jira import JIRA


class JiraComment:
    """Class constructor."""
    def __init__(self, jira_issue):
        with open('secret.json', 'r') as secret_file:
            data = json.load(secret_file)
            self.jira_url = data["jira_url"]
            self.jira_username = data["jira_username"]
            self.jira_token = data["jira_token"]
            self.jira_issue = jira_issue
            self.comments_bodys = None
            self.comment_length = None
            self.comment_id = None
            self.comment = None
            self.jira = JIRA(options={'server': self.jira_url},
                             basic_auth=(self.jira_username, self.jira_token))

    def get_comment_id(self, comment_index):
        """Get the comment ID from the Jira issue using index."""
        self.comments_bodys = self.jira.issue(self.jira_issue, fields='comment')
        self.comment_length = len(self.comments_bodys .fields.comment.comments)
        print(self.comments_bodys .fields.comment.comments)
        if self.comment_length == 0:
            print("Your Jira has no comment yet, please add a comment first.")
            return False, "Your Jira has no comment yet, please add a comment first"
        elif comment_index > self.comment_length or comment_index <= 0:
            print("Your Jira comment index is out of range.")
            return False, "Your Jira comment index is out of range."
        else:
            self.comment_id = self.comments_bodys .fields.comment.comments[comment_index-1].id
            return  True, self.comment_id


    def get_comment_content(self, jira_issue, comment_id):
        """Get the comment content to modify."""
        comment = self.jira.comment(jira_issue, comment_id)
        return  comment.body

    def update_comment(self, jira_issue, comment_id, edit_comment):
        """Send the Update comment to the Jira issue. """
        self.comment = self.jira.comment(jira_issue, comment_id)
        self.comment.update(body=edit_comment)

    def add_comment(self, jira_issue, comment_send):
        """Add new comment to the Jira issue"""
        self.jira.add_comment(jira_issue, comment_send)

    def attach_file(self, jira_issue, file_path):
        """Load a file as an attachment to Jira. """
        test = self.jira.add_attachment(issue=jira_issue, attachment=file_path)
        print(test)

def main():
    FILE_PATH = 'testfile.txt'
    JIRA_ISSUE = "WOLK-580"
    TEST = JiraComment(JIRA_ISSUE)
    COMMENT_LIST = TEST.get_comment_id(2)
    print(COMMENT_LIST[0], '  ', COMMENT_LIST[1])
    COMMENT_ID = COMMENT_LIST[1]
    print(COMMENT_ID)
    COMMENT_BODY = TEST.get_comment_content(JIRA_ISSUE, COMMENT_ID)
    print(COMMENT_BODY)
    MODIFY_COMMENT = COMMENT_BODY + "Add comment, even a table can be added "
    TEST.update_comment(JIRA_ISSUE, COMMENT_ID, MODIFY_COMMENT)
    COMMENT_TO_SEND = "Adding new comment"
    TEST.add_comment(JIRA_ISSUE, COMMENT_TO_SEND)
    TEST.attach_file(JIRA_ISSUE, FILE_PATH)

if __name__ == "__main__":
    main()
    



