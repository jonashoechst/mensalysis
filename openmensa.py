#!/usr/bin/env python3
import csv
import requests
import datetime
import sys
import argparse

ENDPOINT = "https://openmensa.org/api/v2/"

csv_fields = ["id", "mensa_id", "date", "name",
              "category", "prices_students", "notes"]


class MealRequestError(RuntimeError):
    def __init__(self, mensa_id, day, status_code):

        super().__init__(
            f"Request for mensa {mensa_id} on {day.strftime('%Y-%m-%d')} failed: {status_code}")

        self.mensa_id = mensa_id
        self.day = day
        self.status_code = status_code


def get_meals(mensa_id: int, day: datetime.date):
    day_string = day.strftime("%Y-%m-%d")

    resp = requests.get(
        url=f"{ENDPOINT}/canteens/{mensa_id}/days/:{day_string}/meals/")

    if resp.status_code != 200:
        raise MealRequestError(mensa_id, day, resp.status_code)

    meals = resp.json()

    for meal in meals:
        meal["prices_students"] = meal["prices"]["students"]
        meal.pop("prices", None)

        meal["date"] = day_string
        meal["mensa_id"] = mensa_id

    return meals


def iter_meals(mensa_id: int, start_date: datetime.date, end_date: datetime.date = datetime.date.today()):
    for n in range(int((end_date - start_date).days)):
        day = start_date + datetime.timedelta(n)
        try:
            day_meals = get_meals(mensa_id, day)
            for meal in day_meals:
                yield meal
        except MealRequestError as err:
            sys.stdout.write(f"{err}\n")

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download data from openmensa.org")

    parser.add_argument("mensa_id",
                        type=int,
                        help="Id of the mensa to query")
    parser.add_argument("--start_date",
                        default=datetime.date.today(),
                        type=lambda s: datetime.datetime.strptime(
                            s, '%Y-%m-%d').date(),
                        help="First day of menu download")
    parser.add_argument("--end_date",
                        default=datetime.date.today(),
                        type=lambda s: datetime.datetime.strptime(
                            s, '%Y-%m-%d').date(),
                        help="Last day of menu download")
    parser.add_argument("--out",
                        default=None,
                        help="Last day of menu download")

    args = parser.parse_args()

    csv_file = open(args.out, "a") if args.out else sys.stdout

    csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
    csv_writer.writeheader()

    for meal in iter_meals(args.mensa_id, args.start_date, args.end_date):
        csv_writer.writerow(meal)

    csv_file.close()
