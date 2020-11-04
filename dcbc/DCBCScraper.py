#!/usr/bin/env python
import csv
import time
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
# If Cloudflare ever comes up...
try:
    import cloudscraper
    requests.session = cloudscraper.create_scraper
except:
    pass


class DrugCheckingBCScraper:
    ACTION_PAGINATE = "sbcd-paginate"
    ACTION_FILTER = "sbcd-filter"

    def __init__(self, human_readable=False):
        self.base_url = "https://drugcheckingbc.ca/"
        self.ajax_url = "wp-admin/admin-ajax.php"
        self.url = self.base_url + self.ajax_url
        self.session = requests.session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
                "referer": "https://drugcheckingbc.ca/results/",
                "accept": "*/*",
                "authority": "drugcheckingbc.ca",
            }
        )
        self.field_cache = None
        self.human_readable = human_readable

    @property
    def entry_count(self):
        return int(
            self.session.get(self.url, params={"action": self.ACTION_FILTER}).json()[
                "count"
            ]
        )

    def get_page(self, page_number=1):
        if page_number == 1:
            return self.__process_rows__(
                self.session.post(
                    self.url, data={"action": self.ACTION_FILTER, "filters": {}}
                ).json()["rows"]
            )
        else:
            return self.__process_rows__(
                self.session.post(
                    self.url,
                    data={
                        "action": self.ACTION_PAGINATE,
                        "page": page_number,
                        "filters": {},
                    },
                ).json()["rows"]
            )

    def __process_rows__(self, row_data):
        result = []
        soup = BeautifulSoup(row_data, features="html.parser")
        for row in soup.select("tr"):
            current_entry = {}
            cells = row.find_all("td")
            for cell in cells:
                current_field_class = cell["class"][0]
                if current_field_class in self.fields.keys():
                    if current_field_class == "ftir_spec_group":
                        contents = cell.get_text(separator="\n").split("\n")
                    else:
                        contents = cell.get_text(strip=True)

                    if contents == "Positive":
                        contents = True
                    elif contents == "Negative":
                        contents = False

                    cur_key = cell["class"][0]
                    if self.human_readable:
                        cur_key = self.fields[cur_key]

                    current_entry[cur_key] = contents
            result.append(current_entry)

        return result

    # If the table structure changes, let's make sure we're getting our fields correct.
    @property
    def fields(self):
        if self.field_cache:
            return self.field_cache

        row = (
            self.session.post(
                self.url, params={"action": self.ACTION_FILTER, "filters": {}}
            )
            .json()["rows"]
            .strip()
            .split("<tr>")[1]
        )  # First entry is always empty. Silly.
        fields = {}
        for td in row.split("td"):
            if ">" in td:
                td = td[: td.index(">")].strip()
                if len(td) == 0 or td == None:
                    continue
                field_tearup = list(
                    filter(lambda x: len(x) > 3, [x for x in td.split("=")])
                )
                fields[field_tearup[1].split("'")[1]] = field_tearup[-1]
        self.field_cache = fields
        return self.field_cache


if __name__ == "__main__":
    scraper = DrugCheckingBCScraper()
    fields = scraper.fields
    cur_date = str((datetime.utcnow() - timedelta(hours=8)).strftime("%Y-%m-%d"))

    artifact_dir = os.path.abspath(os.path.join(os.getcwd(), "artifacts"))
    if not os.path.exists(artifact_dir):
        os.makedirs(artifact_dir)

    with open(os.path.join(artifact_dir, "DrugCheckingBC Full Data - " + cur_date + ".csv"), "w") as csvf:
        csv_file = csv.writer(csvf, quoting=csv.QUOTE_ALL)
        csv_file.writerow([x.replace("'", "") for x in fields.values()])

        test_results = []
        for x in range(1, int(scraper.entry_count / 50) + 1):
            for attempt_number in range(1, 5):
                try:
                    print("Retrieving page {0}. Test result total: {1}".format(x, len(test_results)))
                    res = scraper.get_page(x)
                    csv_file.writerows([result.values() for result in res])
                    test_results += res
                    break
                except Exception as e:
                    print("Need to delay a moment...", e)
                    time.sleep(10 * attempt_number)
                    pass
