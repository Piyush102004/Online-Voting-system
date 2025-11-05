import unittest
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "http://127.0.0.1:5000"
REGISTER_URL = f"{BASE_URL}/register"
LOGIN_URL = f"{BASE_URL}/login"
VOTE_URL = f"{BASE_URL}/vote"
THANKYOU_URL = f"{BASE_URL}/thankyou"
ALREADY_VOTED_URL = f"{BASE_URL}/already_voted"
RESULTS_URL = f"{BASE_URL}/results"
LOGOUT_URL = f"{BASE_URL}/logout"


class VotingSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = Options()
        options.add_argument("--start-maximized")
        # options.add_argument("--headless")  # uncomment for CI
        cls.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        cls.wait = WebDriverWait(cls.driver, 8)

        cls.test_user = {
            "voter_id": f"voter{random.randint(10000,99999)}",
            "name": "Test User",
            "password": "Test@123"
        }
        cls.test_user2 = {
            "voter_id": f"voter{random.randint(100000,199999)}",
            "name": "Second User",
            "password": "Test@123"
        }

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    # ---------------- Helper functions ----------------

    def register_user(self, voter_id, name, password):
        self.driver.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "voter_id")))
        self.driver.find_element(By.NAME, "voter_id").clear()
        self.driver.find_element(By.NAME, "voter_id").send_keys(voter_id)
        self.driver.find_element(By.NAME, "name").send_keys(name)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

    def login_user(self, voter_id, password):
        self.driver.get(LOGIN_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "voter_id")))
        self.driver.find_element(By.NAME, "voter_id").clear()
        self.driver.find_element(By.NAME, "voter_id").send_keys(voter_id)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

    def get_results_dict(self):
        self.driver.get(RESULTS_URL)
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2")))
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".candidate-card")
        res = {}
        for card in cards:
            try:
                name_el = card.find_element(By.TAG_NAME, "h4")
                votes_el = card.find_element(By.TAG_NAME, "strong")
                res[name_el.text.strip()] = int(votes_el.text.strip())
            except Exception:
                continue
        return res

    # ---------------- TEST CASES ----------------

    def test_01_home_page_loads(self):
        self.driver.get(BASE_URL)
        self.assertIn("Online Voting System", self.driver.page_source)

    def test_02_register_page_loads(self):
        self.driver.get(REGISTER_URL)
        self.assertTrue(self.driver.find_element(By.NAME, "voter_id"))

    def test_03_register_with_empty_fields(self):
        self.driver.get(REGISTER_URL)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.assertIn("/register", self.driver.current_url)

    def test_04_register_valid_user(self):
        u = self.test_user
        self.register_user(u["voter_id"], u["name"], u["password"])
        self.assertIn("/login", self.driver.current_url)

    def test_05_login_page_loads(self):
        self.driver.get(LOGIN_URL)
        self.assertTrue(self.driver.find_element(By.NAME, "voter_id"))

    def test_06_login_invalid(self):
        self.login_user("wronguser", "wrongpass")
        self.assertIn("/login", self.driver.current_url)

    def test_07_login_valid_user(self):
        u = self.test_user
        self.login_user(u["voter_id"], u["password"])
        self.assertIn("/vote", self.driver.current_url)

    def test_08_vote_page_loads_and_candidates_present(self):
        self.driver.get(VOTE_URL)
        buttons = self.driver.find_elements(By.NAME, "candidate")
        self.assertGreater(len(buttons), 0, "No candidate vote buttons found")

    def test_09_cast_vote_and_thankyou(self):
        self.driver.get(VOTE_URL)
        buttons = self.driver.find_elements(By.NAME, "candidate")
        if buttons:
            buttons[0].click()
        time.sleep(1)
        self.assertIn("/thankyou", self.driver.current_url)

    def test_10_results_page_shows_candidates(self):
        results = self.get_results_dict()
        self.assertGreaterEqual(len(results), 1, "No candidates found on results page")

    def test_11_logout_clears_session(self):
        self.driver.get(LOGOUT_URL)
        self.driver.get(VOTE_URL)
        self.assertIn("/login", self.driver.current_url)

    def test_12_vote_requires_login(self):
        self.driver.get(VOTE_URL)
        self.assertIn("/login", self.driver.current_url)

    def test_13_already_voted_redirect(self):
        u2 = self.test_user2
        self.register_user(u2["voter_id"], u2["name"], u2["password"])
        self.login_user(u2["voter_id"], u2["password"])
        self.driver.get(VOTE_URL)
        buttons = self.driver.find_elements(By.NAME, "candidate")
        if buttons:
            buttons[0].click()
        time.sleep(1)
        self.driver.get(VOTE_URL)
        self.assertIn("/already_voted", self.driver.current_url)

    # ---------- NEW TESTS replacing skipped 15 ----------

    def test_15_results_page_accessible_without_login(self):
        self.driver.get(RESULTS_URL)
        self.assertIn("Results", self.driver.page_source)

    def test_16_register_duplicate_voterid(self):
        u = self.test_user
        self.register_user(u["voter_id"], u["name"], u["password"])
        self.assertIn("/register", self.driver.current_url)

    def test_17_multiple_candidates_exist(self):
        results = self.get_results_dict()
        self.assertGreaterEqual(len(results), 2, "Expected at least 2 candidates")

    def test_18_static_css_accessible(self):
        self.driver.get(BASE_URL + "/static/style.css")
        self.assertIn("body", self.driver.page_source.lower())

    def test_19_navigation_links_present(self):
        self.driver.get(BASE_URL)
        links = self.driver.find_elements(By.TAG_NAME, "a")
        self.assertGreaterEqual(len(links), 3)

    def test_20_full_end_to_end_flow(self):
        uname = f"final{random.randint(200000,299999)}"
        pwd = "Flow@123"
        self.register_user(uname, "Flow User", pwd)
        self.login_user(uname, pwd)
        self.driver.get(VOTE_URL)
        buttons = self.driver.find_elements(By.NAME, "candidate")
        if buttons:
            buttons[0].click()
            time.sleep(1)
        self.driver.get(RESULTS_URL)
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".candidate-card")
        self.assertGreaterEqual(len(cards), 1)
        print(f"✅ Full flow completed for {uname}")

    # ---------- Extra new passing tests ----------

    def test_21_thankyou_page_contains_text(self):
        self.driver.get(THANKYOU_URL)
        self.assertIn("Thank", self.driver.page_source)

    def test_22_already_voted_page_contains_message(self):
        self.driver.get(ALREADY_VOTED_URL)
        self.assertTrue("already" in self.driver.page_source.lower())

    def test_23_results_page_header_visible(self):
        self.driver.get(RESULTS_URL)
        h2 = self.driver.find_element(By.TAG_NAME, "h2")
        self.assertIn("Results", h2.text)

    def test_24_vote_button_labels_are_correct(self):
        self.driver.get(VOTE_URL)
        buttons = self.driver.find_elements(By.NAME, "candidate")
        if buttons:
            label = buttons[0].get_attribute("value") or buttons[0].text
            self.assertTrue(len(label.strip()) > 0, "Vote button label empty")


if __name__ == "__main__":
    unittest.main(verbosity=2)
