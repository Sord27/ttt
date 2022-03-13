#! /usr/bin/env python3
""" Selenium Back Office (Ops Portal) Navigation """
from collections import namedtuple
import typing
import pathlib
import requests
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions
import time

DOWNLOAD_FOLDER = pathlib.Path("/", "tmp")
BACKOFFICE_URLS = {
    "circle1": "https://circle1-ops.circle.siq.sleepnumber.com/",
    "dev21": "https://dev21-ops.dev.siq.sleepnumber.com/",
    "dev22": "https://dev22-ops.dev.siq.sleepnumber.com/",
    "dev23": "https://dev23-ops.dev.siq.sleepnumber.com/",
    "dev24": "https://dev24-ops.dev.siq.sleepnumber.com/",
    "ops21": "https://ops21-ops.dev.siq.sleepnumber.com/",
    "prod": "https://prod-ops.sleepiq.sleepnumber.com/",
    "qa21": "https://qa21-ops.dev.siq.sleepnumber.com/",
    "qa22": "https://qa22-ops.dev.siq.sleepnumber.com/",
    "qa23": "https://qa23-ops.dev.siq.sleepnumber.com/",
    "stage": "https://stage-ops.stage.siq.sleepnumber.com/",
    "test": "https://test-ops.test.siq.sleepnumber.com/",
}


class Page:
    HOME = "home"
    APPS = "apps"
    PEOPLE = "people"
    SETTINGS = "settings"
    SUPPORT = "support"
    BAMADMIN = "bamadmin"

class SearchCriteria:
    ACCOUNT_NAME = 'Account name'
    FIRST_NAME = 'First name'
    LAST_NAME = 'Last name'
    LOGIN = 'Login'
    MAC_ADDRESS = 'MacAddress'

class DeviceOption():
    RESET = "Reset"
    CALIBRATE = "Calibrate"
    PUT_BACK_IN_BED = "Put Back In Bed"

class BamAdminTab():
    USERS = "Users"
    BINARIES = "Binaries"
    TOOLS = "Tools"
    OPS = "Ops"
    CONSOLE = "Console"
    MONITOR = "Monitor"
    EVENTS = "Events"
    DASH = "Dash"
    BLOH = "Bloh"
    PROMOTE = "Promote"
    LEVELS = "Levels"
    BETA = "Beta"

class BamAdminButton():
    CALIBRATE = "Calibrate"
    RESET_USER_DATA = "Reset User Data"
    RESTART = "Restart"
    UPDATE_SW = "Update SW"
    SEND_RPC = "Send RPC"
    RECONNECT = "Reconnect"
    RAW_DATA = "Raw Data"

class SettingsTabOption():
    USERS = "Users"
    DEVICES = "Devices"
    NETWORK = "Network"
    ACCOUNT = "Account"

class AppsTabOption():
    BED_EXIT = "Bed Exit"
    SLEEP = "Sleep"
    TRENDS = "Trends"
    LIVE_VIEW = "Live View"
    LAB_VIEW = "Lab View"

class SleepTabButton():
    COMPUTE_NEW_FOR_USER = "Computer new for user!"
    EDIT_SELECTED_SLEEP_SESSION = "Edit the selected sleep session"
    SEND_SLEEP_INFO = "Send Sleep Info to Device"
    SEND_SLEEPER_INFO = "Send Sleeper Info to Device"


def normalize_mac_address(mac_address: str) -> str:
    """ Normalize a MAC Address
    :param mac_address: MAC address to normalize
    :return: A mac address with no colons or lowercase letters"""
    return mac_address.replace(":", "").upper()


class BackOffice:
    """Interact with various features in the Backoffice administration page"""
    def __init__(self,
                 environment: str,
                 admin_username: str,
                 admin_password: str,
                 headless: bool = True,
                 verbosity: int = 0):
        """Backoffice class. Requires chromedriver to be installed
        :param environment: The environment to connect to
        :param admin_username: Backoffice username
        :param admin_password: Backoffice password
        :param headless: Run selenium headless. If verbosity is greater than 2,
            selenium will not be run headless.
        :param verbosity: Verbosity level
        """
        self.verbosity = verbosity
        if self.verbosity:
            print("Starting Selenium Chrome Session")
        options = Options()
        options.add_argument("disable-extensions")
        if headless and verbosity < 3:
            options.add_argument("headless")
        options.add_argument("start-maximized")
        options.add_argument("disable-gpu")
        options.add_argument("no-sandbox")
        # Start the chrome selenium driver
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, timeout=30)
        self.backoffice_url = BACKOFFICE_URLS[environment]
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.device_entry = namedtuple("DeviceEntry", [
            "device_id", "last_contact", "app_version", "rfs_version",
            "server", "sensor_information"
        ])
        self.user_entry = namedtuple(
            "UserEntry", ["last_name", "first_name", "login_id", "roles"])

    class ElementIsNotVisible:
        """An expectation for checking the visibility of an existing element
        :param element_id: used to find the element
        :return:
            returns the WebElement once the particular element is visible
            otherwise returns False
        """
        def __init__(self, element_id: str):
            self.element_id = element_id

        def __call__(self, driver):
            element = driver.find_element_by_id(
                self.element_id)  # Finding the referenced element
            if not element.is_displayed():
                return element
            return False

    def __del__(self):
        """Close selenium driver"""
        self.driver.close()

    def wait_for_progress_indicator(self):
        """Wait for the progress indicator to disappear, indicating the action
        has completed"""
        self.wait.until(self.ElementIsNotVisible("progress_indicator"))

    def login(self):
        """Login into backoffice """
        if self.verbosity:
            print("Logging in to Backoffice")
        self.driver.get(
            "{url}bam/pages/logon.jsp".format(url=self.backoffice_url))
        assert self.driver.title == "BAM -- Home"
        # Find the login fields and button
        username_field = self.driver.find_element_by_id("username")
        password_field = self.driver.find_element_by_id("password")
        submit_button = self.driver.find_element_by_class_name("login-button")
        # Login
        username_field.clear()
        password_field.clear()
        username_field.send_keys(self.admin_username)
        password_field.send_keys(self.admin_password)
        submit_button.click()
        # Check for login
        assert self.driver.title == "BAM -- Admin"
        assert self.driver.current_url == "{url}bam/admin/main.jsf".format(
            url=self.backoffice_url)

    def search(self,
               query: str,
               search_criteria: str = SearchCriteria.MAC_ADDRESS):
        """Perform a search in Backoffice
        :param query: Search query
        :param search_criteria: Search criteria button
        :return: Tuple of users and devices
        """
        if self.verbosity:
            print("Searching for {query}".format(query=query))
        # Get the query form elements
        search_form = self.driver.find_element_by_id("searchForm")
        radio_button = search_form.find_element_by_xpath(
            f"//input[@type='radio'][following-sibling::label[contains(text(), '{search_criteria}')]]")
        search_field = search_form.find_element_by_id("searchForm:searchInput")
        submit_button = search_form.find_element_by_xpath("//input[@type='submit']")
        # Select search criteria
        radio_button.click()
        # Run the Search
        search_field.clear()
        search_field.send_keys(query)
        submit_button.click()
        self.wait_for_progress_indicator()
        # Get the search results
        user_entries = self.get_user_table()
        device_entries = self.get_device_table()
        return user_entries, device_entries

    def select_user_by_login(self, login: str):
        """Selects the user by login from the user table
        :param login: The user login name
        """
        if self.verbosity > 1:
            print("Selecting user: {user}".format(user=login))
        result = self.driver.find_element_by_xpath(
            "//*[normalize-space(text())='{login}']".format(login=login))
        result.click()
        self.wait_for_progress_indicator()

    def select_device_by_mac_address(self, mac_address: str):
        """Selects the device by mac address from the device table
        :param mac_address: The mac address
        """
        if self.verbosity > 1:
            print("Selecting device: {device}".format(device=mac_address))
        mac_address = normalize_mac_address(mac_address=mac_address)
        result = self.driver.find_element_by_xpath(
            "//*[normalize-space(text())='{mac_address}']".format(
                mac_address=mac_address))
        result.click()
        self.wait_for_progress_indicator()

    def get_user_table(self) -> dict:
        """Gets the user table as a dictionary containing the information
        :return:
            returns the user table with the login id as the key and
            the user table results as a namedtuple
        """
        if self.verbosity > 1:
            print("Get list of current users")
        return self._get_results(self.user_entry, "userTable", "login_id")

    def get_device_table(self) -> dict:
        """Gets the device table as a dictionary containing the information
        :return:
            returns the device table with the mac address as the key and
            the device table results as a namedtuple
        """
        if self.verbosity > 1:
            print("Get list of current devices")
        return self._get_results(self.device_entry, "devicesTable",
                                 "device_id")

    def _get_results(self, entry_type: namedtuple, table_id: str,
                     identifier: str) -> dict:
        """Gets the query result a table
        :param entry_type: namedtuple entry type (device_entry/user_entry)
        :param table_id: html tag ID
        :param identifier: the distinct identifier to construct the return
            dictionary
        :return:
            entries: a dictionary containing keys as the given identifier
            with entry_type namedtuple values
        """
        table = self.driver.find_element_by_xpath(
            "//tbody[contains(@id,'{}')]".format(table_id))
        results = table.find_elements_by_tag_name("tr")
        entries = {}
        for entry in results:
            columns = entry.find_elements_by_tag_name("div")
            column_values = map(lambda column: column.text, columns)
            entry = entry_type(*column_values)
            entries[getattr(entry, identifier)] = entry
        return entries

    def save_software(self,
                      app_version=None,
                      rfs_version=None,
                      manifest_name=None,
                      device_mode=None):
        """Saves the software version
        :param app_version: The bammit application version
        :param rfs_version: The RFS version
        :param device_mode: The device mode ()
        """
        if self.verbosity:
            print("Set software. APP: {app}  RFS: {rfs}  Manifest: {manifest} Mode: {mode}".format(
                app=app_version, rfs=rfs_version, manifest=manifest_name, mode=device_mode))
        device_info_form = self.driver.find_element_by_id("deviceInfoForm")

        device_info = device_info_form.find_element_by_xpath(
            "//td[text()='Device Info:']/following-sibling::td").text
        device_version = device_info_form.find_element_by_xpath(
            "//td[text()='Device Version:']/following-sibling::td").text
        bammit_version_dropdown = Select(
            device_info_form.find_element_by_xpath(
                "//td[text()='Bammit Version:']/following-sibling::td//select")
        )
        rfs_version_dropdown = Select(
            device_info_form.find_element_by_xpath(
                "//td[text()='RFS Version:']/following-sibling::td//select"))
        manifest_name_dropdown = Select(
            device_info_form.find_element_by_xpath(
                "//td[text()='Manifest Version:']/following-sibling::td//select"))
        device_mode_dropdown = Select(
            device_info_form.find_element_by_xpath(
                "//td[text()='Device Mode:']/following-sibling::td//select"))
        save_button = device_info_form.find_element_by_xpath(
            "//input[@value='Save']")
        if app_version is not None:
            bammit_version_dropdown.select_by_value(app_version)
        if rfs_version is not None:
            rfs_version_dropdown.select_by_value(rfs_version)
        if manifest_name is not None:
            manifest_name_dropdown.select_by_value(manifest_name)
        if device_mode is not None:
            device_mode_dropdown.select_by_value(device_mode)
        save_button.click()
        self.wait_for_progress_indicator()

    def update_software(self):
        """Locates and clicks on update software button
        """
        if self.verbosity:
            print("Trigger device update")
        update_software_link = self.driver.find_element_by_link_text(
            "Update SW")
        update_software_link.click()
        self.wait_for_progress_indicator()

    def save_software_by_mac(self,
                             mac_address: str,
                             app_version: str = None,
                             rfs_version: str = None,
                             manifest_name: str = None,
                             device_mode: str = None):
        """
        Save software version using MAC address
        :param mac_address: MAC address of pump
        :param app_version: Bammit App Version
        :param rfs_version: RFS Version
        :param device_mode: Device mode
        """
        _, device_entries = self.search(mac_address, search_criteria=SearchCriteria.MAC_ADDRESS)
        mac_address = normalize_mac_address(mac_address=mac_address)
        if mac_address not in device_entries:
            raise Exception("MAC Address not found")
        self.select_device_by_mac_address(mac_address)
        self.save_software(app_version=app_version,
                           rfs_version=rfs_version,
                           manifest_name=manifest_name,
                           device_mode=device_mode)

    def save_software_by_login(self,
                               login: str,
                               app_version: str = None,
                               rfs_version: str = None,
                               device_mode: str = None):
        """ Save software version using login
        :param login: Username of account
        :param app_version: Bammit App Version
        :param rfs_version: RFS Version
        :param device_mode: Device Mode"""
        user_entries, _ = self.search(login, search_criteria=SearchCriteria.LOGIN)
        if login not in user_entries:
            raise Exception("User not found")
        self.select_user_by_login(login)
        device_entries = self.get_device_table()
        for device in device_entries:
            self.select_device_by_mac_address(device)
            self.save_software(app_version=app_version,
                               rfs_version=rfs_version,
                               device_mode=device_mode)

    def update_software_by_mac(self, mac_address: str):
        """ Update software version using MAC address """
        _, device_entries = self.search(mac_address, search_criteria=SearchCriteria.MAC_ADDRESS)
        mac_address = normalize_mac_address(mac_address=mac_address)
        if mac_address not in device_entries:
            raise Exception("MAC Address not found")
        self.select_device_by_mac_address(mac_address)
        self.update_software()

    def update_software_by_login(self, login: str):
        """ Update software version using login """
        user_entries, _ = self.search(login, search_criteria=SearchCriteria.LOGIN)
        if login not in user_entries:
            raise Exception("User not found")

        self.select_user_by_login(login)
        device_entries = self.get_device_table()
        for device in device_entries:
            self.select_device_by_mac_address(device)
            self.update_software()

    def become_user_by_mac(self, mac_address: str):
        """ Become user based on mac address """
        _, device_entries = self.search(mac_address, search_criteria=SearchCriteria.MAC_ADDRESS)
        mac_address = normalize_mac_address(mac_address=mac_address)
        if mac_address not in device_entries:
            raise Exception("MAC Address not found")
        self.select_device_by_mac_address(mac_address)
        become_user_button = self.driver.find_element_by_xpath(
            "//*[@type='button' and @value='Become User']")
        become_user_button.click()
        self.wait_for_progress_indicator()

    def navigate(self, page):
        """ Navigates to selected page
        :param page: string from the Page constants
        """
        pages = {
            Page.HOME: "/bam/pages/apps/home.jsf",
            Page.APPS: "/bam/pages/apps/apps.jsf",
            Page.PEOPLE: "/bam/pages/people/people.jsf",
            Page.SETTINGS: "/bam/pages/settings/settings.jsf",
            Page.SUPPORT: "/bam/pages/support/support.jsf",
            Page.BAMADMIN: "/bam/admin/main.jsf"
        }

        if self.driver.current_url.endswith(pages[page]):
            return  # do nothing, already on the page

        page = self.driver.find_element_by_xpath(f"//a[@href='{pages[page]}']")
        page.click()
        self.wait_for_progress_indicator()

    def select_sleeper(self, full_name):
        """ Selects sleeper based on full sleeper name
        :param full_name: first and last name of sleeper
        """
        sleeper_list = Select(
            self.driver.find_element_by_xpath(
                "//*[@id='j_id85:patientRow:0:j_id122']/select"))

        sleeper_list.select_by_visible_text(full_name)

    def download_raw1k(self, date):
        """ Downloads raw1k file of selected date into download folder
        :param date: datetime obj
        :return:
            returns a pathlib object of the downloaded file
        """
        # Select Date
        calendar = self.driver.find_element_by_xpath(
            "//td[@class='rich-calendar-month']/div")
        calendar.click()
        self.wait_for_progress_indicator()

        self.driver.find_element_by_xpath(f"//div[text()='{date:%b}']").click()
        self.driver.find_element_by_xpath(f"//div[text()='{date:%Y}']").click()
        self.driver.find_element_by_xpath("//span[text()='OK']").click()
        self.driver.find_element_by_xpath(
            f"//div[@class='sleep-session-calendar-day' and text()='{date:%d}']"
        ).click()
        self.wait_for_progress_indicator()

        # Get File Download Link
        raw1k_file_link = self.driver.find_element_by_link_text(
            "Raw File").get_attribute("href")

        # Pass along driver cookies
        cookies = self.driver.get_cookies()
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie["name"], cookie["value"])

        # Get File
        response = session.get(raw1k_file_link, allow_redirects=True)

        filename = DOWNLOAD_FOLDER / f"{date:%Y%m%d}.raw1k"
        with open(filename, "wb") as file:
            file.write(response.content)

        return filename

    def wait_until_element_is_located_by_xpath(self, xpath, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            expected_conditions.presence_of_element_located((By.XPATH, xpath))
        )

    def navigate_to_bamadmin_tab(self, tab):
        """ Navigates to BamAdmin Page and navigates to desired tab
        :param: tab: desired BamAdminTab to navigate to
        """
        # Navigates to BAM Admin Page
        self.navigate(Page.BAMADMIN)

        # Click on desired tab
        settings_tab = self.driver.find_element_by_xpath(f"//td[text()='{tab}']")

        if settings_tab.get_attribute("class").strip().endswith("rich-tab-active"):
            return  # do nothing, already on the tab

        settings_tab.click()
        self.wait_for_progress_indicator()


    def navigate_to_settings_tab(self, tab):
        """ Navigates to Settings Page and navigates to desired tab
        :param: tab: desired SettingsTabOption to navigate to
        """
        # Navigates to Settings Page
        self.navigate(Page.SETTINGS)

        # Click on desired tab
        settings_tab = self.driver.find_element_by_xpath(f"//td[text()='{tab}']")
        settings_tab.click()
        self.wait_for_progress_indicator()

    def navigate_to_apps_tab_option(self, tab):
        """ Navigates to desired Apps page tab
        :param: tab: value of AppsTabOption to click
        """
        apps_tab = self.wait_until_element_is_located_by_xpath(f"//td[text() = '{tab}']")
        apps_tab.click()
        self.wait_for_progress_indicator()

    def click_on_device_option(self, device_id, option):
        """ Navigates to Settings Page, clicks on device, and chooses desired option
        :param: device_id: MAC Address of device (64DBAXXXXXX)
        :param: option: value of desired button to click
        """
        # Go to Devices tab
        self.navigate_to_settings_tab(SettingsTabOption.DEVICES)

        # Click on Device
        device_id = ":".join(device_id[i:i+2] for i in range(0, 12, 2)).upper()
        device = self.driver.find_element_by_xpath(f"//div[contains(@id, itemTableDev) and text() = '{device_id}']")
        device.click()

        # Click desired Device Option
        # button = device.find_element_by_xpath(f"//input[@type='button' and @value='{option}']")
        button = self.wait_until_element_is_located_by_xpath(f"//input[@type='button' and @value='{option}']")
        button.click()

    def click_on_apps_sleep_button(self, button):
        """ Clicks on desired button in Apps Page - Sleep Tab
        :param: button: desired SleepTabButton to click
        """
        button = self.driver.find_element_by_xpath(f"//input[@value = '{button}']")
        button.click()
        self.wait_for_progress_indicator()

    def click_on_bamadmin_button(self, button):
        """ Clicks on desired BAMAdmin button
        :param: button: desired BamAdminButton to click
        """
        # Click on desired button
        button = self.driver.find_element_by_xpath(f"//*[text()='{button}']")
        button.click()
        self.wait_for_progress_indicator()

    def get_preferences(self, mac_address):
        """ Gets preferences from server
        :param: mac_address: mac address to get preferences for
        :return:
            return preference
        """
        mac_address = mac_address.lower().replace(":", "")

        device_text_box = self.driver.find_element_by_xpath('//input[@type="text" and contains(@name, "loadPreferencesForm")]')
        device_text_box.clear()
        device_text_box.send_keys(mac_address)

        get_prefs_button = self.driver.find_element_by_xpath('//input[@type="submit" and @value="Get Preferences"]')
        get_prefs_button.click()

        for i in range(20):
            try:
                results_text = self.wait_until_element_is_located_by_xpath('//span[@id="propertiesResults"]/table/tbody/tr/td')
                if results_text.text == "Got device preferences from DB":
                    preference_box = self.driver.find_element_by_xpath('//textarea[contains(@name, "preferenceProfileText")]')
                    return preference_box.text
                if results_text.text == "Device by given MAC not found":
                    raise ValueError("Device not found:", mac_address)
            except (StaleElementReferenceException, NoSuchElementException, TimeoutException) as e:
                pass
            finally:
                time.sleep(0.1)

        raise ValueError(f"Preferences not received for {mac_address}")

    def set_preferences(self, mac_address, preferences):
        """ Sets preferences to server and sends them to the device
        :param: mac_address: mac address to set preferences for
        :param: preferences: preferences text to set
        :return:
            returns success of setting preference
        """
        mac_address = mac_address.lower().replace(":", "")

        device_text_box = self.driver.find_element_by_xpath('//input[@type="text" and contains(@name, "loadPreferencesForm")]')
        device_text_box.clear()
        device_text_box.send_keys(mac_address)

        preference_box = self.driver.find_element_by_xpath('//textarea[contains(@name, "preferenceProfileText")]')
        preference_box.clear()
        preference_box.send_keys(preferences)

        get_prefs_button = self.driver.find_element_by_xpath('//input[@type="button" and @value="Send Pref to Device"]')
        get_prefs_button.click()

        for i in range(10):
            try:
                results_text = self.wait_until_element_is_located_by_xpath('//span[@id="propertiesResults"]/table/tbody/tr/td')
                if results_text.text == "Send preferences succeeded":
                    return True
                if results_text.text == "Preferences profile does not sent - device is offline":
                    return False
            except (StaleElementReferenceException, NoSuchElementException, TimeoutException) as e:
                pass
            finally:
                time.sleep(0.1)

        raise ValueError(f"Preferences not sent for {mac_address}")
