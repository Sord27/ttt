import argparse
import atexit
import logging
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait


logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class Page:
    LOGIN = "login"
    SUMMARY = "summary"
    OUTLET = "outlet"


class ControlActions:
    TURN_ON=0
    TURN_OFF=1
    REBOOT=2
    CANCEL_PENDING_COMMAND=3


class PduRemoteManagement:
    """Interact with various features in the PDU Remote Management administration page"""
    def __init__(self,
                 pdu_url: str,
                 admin_username: str,
                 admin_password: str,
                 headless: bool = True,
                 verbosity: int = 0):
        """PduRemoteManagement class. Requires chromedriver to be installed
        :param admin_username: PduRemoteManagement username
        :param admin_password: PduRemoteManagement password
        :param headless: Run selenium headless. If verbosity is greater than 2,
            selenium will not be run headless.
        :param verbosity: Verbosity level
        """
        self.verbosity = verbosity
        if self.verbosity > 1:
            logging.info("Starting Selenium Chrome Session")
        options = Options()
        options.add_argument("disable-extensions")
        if headless and verbosity < 2:
            options.add_argument("headless")
        options.add_argument("start-maximized")
        options.add_argument("disable-gpu")
        options.add_argument("no-sandbox")

        # Start the chrome selenium driver
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, timeout=30)
        self.pdu_remote_url = pdu_url
        self.admin_username = admin_username
        self.admin_password = admin_password
        atexit.register(self.cleanup)

    def cleanup(self):
        """Close selenium driver"""
        #self.driver.close()
        self.driver.quit()

    def login(self):
        """Login into pdu management """
        if self.verbosity > 1:
            logging.info("Logging in to Pdu Remote Management")
        self.driver.get(
            f"{self.pdu_remote_url}")

        assert self.driver.title.strip() == "PDU Remote Management | Login"

        # Find the login fields and button
        username_field = self.driver.find_element_by_id("username")
        password_field = self.driver.find_element_by_id("password")
        submit_button = self.driver.find_element_by_id("login_sub")
        # Login
        username_field.clear()
        password_field.clear()
        username_field.send_keys(self.admin_username)
        password_field.send_keys(self.admin_password)
        submit_button.click()

        try:
          WebDriverWait(self.driver, 10).until(lambda x: self.driver.title.strip() == "PDU Remote Management")
        except TimeoutException as e:
          pass

        # Check for login
        assert self.driver.title.strip() == "PDU Remote Management"
        assert self.driver.current_url == f"{self.pdu_remote_url}summary.html"

    def logout(self):
        """Logout from pdu management """
        if self.verbosity > 1:
            logging.info("Logout from Pdu Remote Management")

        self.driver.find_element_by_link_text("Logout").click()

        assert "You have logged out Remote Management" in self.driver.page_source

    def navigate(self, page):
        """ Navigates to selected page
        :param page: string from the Page constants
        """
        if self.verbosity > 1:
            logging.info(f"Navigating to page {page}")

        pages = {
            Page.OUTLET: "outlet.html"
        }

        if self.driver.current_url.endswith(pages[page]):
            return  # do nothing, already on the page

        self.driver.get(f"{self.pdu_remote_url}{pages[page]}")

    def apply_control_action(self, action: str, outlets: str):
        """Applies the control action on selected outlets
        :param action: The action
        :param outlets: The outlets numbers
        """
        if self.verbosity:
            logging.info(f"Applying '{action}' to outlet {outlets}")

        control_action_dropdown = Select(
            self.driver.find_element_by_css_selector(
                "[name=ActionSel]")
        )
        actions = {
            "turn_on": ControlActions.TURN_ON,
            "turn_off": ControlActions.TURN_OFF,
            "reboot": ControlActions.REBOOT,
            "cancel": ControlActions.CANCEL_PENDING_COMMAND
        }

        control_action_dropdown.select_by_index(actions[action])

        outlets = outlets.split(",")
        for outlet in outlets:
            self.driver.find_element_by_css_selector(f"[name=ActOut{outlet}]").click()

        self.driver.find_element_by_css_selector("[name=action]").click()
        self.driver.find_element_by_css_selector("[name=action]").click()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", default=None, type=str, required=True, help="Remote url of PDU")
    parser.add_argument("-U", "--user", default="cyber", type=str, required=True, help="Username")
    parser.add_argument("-P", "--password", default="cyber", type=str, required=True, help="Password")
    parser.add_argument("-A", "--control_action", default=None, type=str, required=True, help="Outlet control action")
    parser.add_argument("-O", "--outlets", default=None, type=str, required=True, help="Outlets to perform action on")
    parser.add_argument("-v", "--verbose", default=0, action="count", help="Adjust verbosity")

    args = parser.parse_args()

    pdu_remote = PduRemoteManagement(
        pdu_url=args.url,               # for example "http://172.22.10.19:8080/"
        admin_username=args.user,       # cyber
        admin_password=args.password,   # cyber
        verbosity=args.verbose)

    pdu_remote.login()
    pdu_remote.navigate(Page.OUTLET)
    pdu_remote.apply_control_action(args.control_action, args.outlets)
    pdu_remote.logout()
