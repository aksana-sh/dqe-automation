import time
import pandas as pd
import itertools

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager


class SeleniumWebDriverContextManager:
    def __init__(self):
        self.driver: WebDriver | None = None

    def __enter__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver

    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Failed to quit WebDriver: {e}")
        return


def interact_table(driver):
    """Extract table content and save to CSV"""

    # Load table
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "table"))
        )
        print("HTML report table is visible")
    except TimeoutException:
        print("HTML report table did not load")
        exit()

    # Get table root
    try:
        table = driver.find_element(By.CLASS_NAME, "table")
    except NoSuchElementException:
        print("HTML report table root not found")
        exit()

    # Get all columns for table
    try:
        columns = table.find_elements(By.CSS_SELECTOR, "g.y-column")
    except NoSuchElementException:
        print("No columns found inside HTML report table")
        exit()
    if not columns:
        print("HTML report table has no columns")
        exit()

    # Extract column headers and cells
    column_headers = []
    column_cells = []

    for col in columns:
        # headers
        try:
            header = col.find_element(By.ID, "header").text.strip()
        except NoSuchElementException:
            header = "Unknown"
        column_headers.append(header)
        # cells
        try:
            cells = col.find_elements(By.CLASS_NAME, "cell-text")
        except NoSuchElementException:
            cells = []
        # filter headers from cell values
        cell_values = [c.text.strip() for c in cells if c.text.strip() != header]
        column_cells.append(cell_values)

    # Transpose columns to rows
    rows = list(zip(*column_cells))

    # Save table content to CSV
    df = pd.DataFrame(rows, columns=column_headers)
    df.to_csv("table.csv", index=False, encoding="utf-8")
    print("Table content successfully saved to table.csv")


def extract_chart_data(doughnut):
    """Extract slice labels and values from doughnut chart"""

    chart_data = []
    try:
        chart_labels = doughnut.find_elements(By.CSS_SELECTOR, "text.slicetext[data-notex='1']")
        for chart_label in chart_labels:
            tspans = chart_label.find_elements(By.TAG_NAME, "tspan")
            category = tspans[0].text.strip()
            value = tspans[1].text.strip()
            chart_data.append([category, value])
    except NoSuchElementException:
        print("No slice labels found")
    return chart_data


def interact_chart(driver):
    """Extract doughnut chart data for all filter combinations."""

    # Check if chart root is visible
    try:
        doughnut = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pielayer"))
        )

        print("Doughnut chart loaded")
    except TimeoutException:
        print("Chart did not load")
        exit()

    # ----------------------------------------------------
    # 1. INITIAL STATE (all selected): take initial screenshot, save doughnut chart data
    # ----------------------------------------------------
    driver.save_screenshot("screenshot0.png")
    chart_data = extract_chart_data(doughnut)
    if chart_data:
        df = pd.DataFrame(chart_data, columns=["Facility Type", "Min Average Time Spent"])
        df.to_csv("doughnut0.csv", index=False, encoding="utf-8")

    # ----------------------------------------------------
    # 2. APPLY FILTERS: take screenshot, save doughnut chart data
    # ----------------------------------------------------
    try:
        legend = driver.find_element(By.CLASS_NAME, "scrollbox")
        filters = legend.find_elements(By.CLASS_NAME, "traces")
    except NoSuchElementException:
        print("No filters found")
        filters = []

    # Map legend_labels to legend_toggles
    filter_map = {}
    for f in filters:
        legend_label = f.find_element(By.CLASS_NAME, "legendtext").text.strip()
        legend_toggle = f.find_element(By.CLASS_NAME, "legendtoggle")
        filter_map[legend_label] = legend_toggle

    legend_labels = list(filter_map.keys())

    # Build filter combinations: singles, pairs, and empty
    combinations = (
            [[label] for label in legend_labels] +
            [list(pair) for pair in itertools.combinations(legend_labels, 2)] +
            [[]]  # all deselected
    )

    # Deselect all filters before loop
    for toggle in filter_map.values():
        toggle.click()
        time.sleep(1)

    # Apply filters (all possible combinations)
    for i, combo in enumerate(combinations, start=1):
        try:
            # Step 1: Enable only filters in combo
            for label in combo:
                filter_map[label].click()
                time.sleep(1)

            # Step 2: take screenshot, save CSV
            combo_name = "_".join(combo) if combo else "AllInactive"
            driver.save_screenshot(f"screenshot{i}.png")

            doughnut = driver.find_element(By.CLASS_NAME, "pielayer")
            chart_data = extract_chart_data(doughnut)

            df = pd.DataFrame(chart_data, columns=["Facility Type", "Min Average Time Spent"])
            df.to_csv(f"doughnut{i}.csv", index=False, encoding="utf-8")

            print(f"Filter combination {combo_name} saved: screenshot{i}.png, doughnut{i}.csv")

            # Step 4: deselect active filters for next iteration
            for label in combo:
                filter_map[label].click()
                time.sleep(1)

        except Exception as e:
            print(f"Failed for combination {combo}: {e}")


if __name__ == "__main__":
    html_file = r"C:\Users\Aksana_Shchukina\Desktop\DQ_Automation\report.html"
    with SeleniumWebDriverContextManager() as driver:
        driver.get(f"file:///{html_file}")
        interact_table(driver)
        interact_chart(driver)
