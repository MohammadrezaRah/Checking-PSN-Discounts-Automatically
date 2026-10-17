import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import time
import os

PROXY = "socks5h://127.0.0.1:10808"

proxies = {
	"http": PROXY,
	"https": PROXY
}

headers = {
	"User-Agent": (
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
		"AppleWebKit/537.36 (KHTML, like Gecko) "
		"Chrome/139.0.0.0 Safari/537.36"
	)
}


def ps_discounts():
	BASE_URL = "https://psprices.com/region-us/collection/all-discounts"

	games = []

	for page in range(1, 3):

		print(f"\nReceiving Page {page} ...")

		params = {
			"ordering": "desc",
			"page": page,
			"rating_logic": "or",
			"show": "games",
			"sort": "likes"
		}

		try:

			response = requests.get(
				BASE_URL,
				params=params,
				headers=headers,
				proxies=proxies,
				timeout=30
			)

			response.raise_for_status()

			print(
				f"Status: {response.status_code} | "
				f"HTML size: {len(response.text)}"
			)

			soup = BeautifulSoup(response.text, "html.parser")

			page_games = []

			for link in soup.select('a[href*="/region-us/game/"]'):

				title_tag = link.select_one("h3")
				discount_tag = link.select_one(
					'[data-test-id="discount-badge"]'
				)
				current_price_tag = link.select_one(
					".text-xl.font-bold"
				)
				old_price_tag = link.select_one(
					".old-price-strike"
				)

				if not title_tag:
					continue

				title = title_tag.get_text(
					" ",
					strip=True
				)

				discount = None

				if discount_tag:
					discount = discount_tag.get_text(
						" ",
						strip=True
					)

					discount = discount.replace("−", "-")

				current_price = None

				if current_price_tag:
					current_price = current_price_tag.get_text(
						" ",
						strip=True
					)

				original_price = None

				if old_price_tag:
					original_price = "$ " + old_price_tag.get_text(
						" ",
						strip=True
					)

				game_url = urljoin(
					"https://psprices.com",
					link.get("href")
				)

				game = {
					"title": title,
					"discount": discount,
					"current_price": current_price,
					"original_price": original_price,
					"url": game_url
				}

				page_games.append(game)

			print(f"Games of page {page}: {len(page_games)}")

			games.extend(page_games)

			# کمی مکث بین درخواست‌ها
			time.sleep(1)

		except Exception as e:

			print(
				f"ERR AT PAGE {page}: {e}"
			)

	# حذف بازی‌های تکراری بر اساس URL

	unique_games = {}

	for game in games:
		unique_games[game["url"]] = game

	games = list(unique_games.values())

	# بررسی تفاوت با فایل قبلی
	json_path = "discounts.json"

	if os.path.exists(json_path):

		with open(
				json_path,
				"r",
				encoding="utf-8"
		) as file:

			old_games = json.load(file)

		if old_games == games:
			print("✅ تغییری در لیست تخفیف‌ها ایجاد نشده است.")
			print("⏹ Going to Stop.")

			exit()

		print("🔄 تغییراتی در لیست تخفیف‌ها ایجاد شده است.")

	# ذخیره لیست جدید در JSON
	with open(
			json_path,
			"w",
			encoding="utf-8"
	) as file:

		json.dump(
			games,
			file,
			ensure_ascii=False,
			indent=4
		)

	print("\n" + "=" * 50)
	print(f"All Games: {len(games)}")
	print("File discounts.json Saved.")
	print("=" * 50)

