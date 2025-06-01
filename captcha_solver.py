import asyncio, httpx, random, cv2, hashlib, math, zlib, base64, time, json, re
from human_cursor import HumanizeMouseTrajectory
import numpy as np


class protonSolver:

	def __init__(self):
		self.hc = HumanizeMouseTrajectory()


	async def solve_challenge(self, captcha_token, proxy="", url="", purpose="signup", useragent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36", cookies={}):

		async with httpx.AsyncClient(http2=True, timeout=15, proxy=proxy if proxy != "" else None, verify=False if "localhost" in proxy else True) as client:
			headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'accept-encoding': 'gzip, deflate, br, zstd', 'accept-language': 'en-US,en;q=0.9,fr;q=0.8,ar;q=0.7', 'cache-control': 'no-cache', 'dnt': '1', 'pragma': 'no-cache', 'priority': 'u=0, i', 'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'none', 'sec-fetch-user': '?1', 'upgrade-insecure-requests': '1', 'user-agent': useragent}
			client.cookies.update(cookies)

			r = await client.get(f"https://verify-api.proton.me/core/v4/captcha?Token={captcha_token}&ForceWebMessaging=1&Dark=true", headers=headers)
			if r.status_code != 200:
				return None
			try:
				k = eval(re.findall(r"sendToken\((.*?)\);", r.text)[0].replace("+response", ""))
			except: #error fetching challenge
				return None

			r = await client.get(f"https://verify-api.proton.me/captcha/v1/api/init?challengeType=2D&parentURL=https%3A%2F%2Fverify-api.proton.me%2Fcore%2Fv4%2Fcaptcha%3FToken%3D{captcha_token}%26ForceWebMessaging%3D1%26Dark%3Dtrue&displayedLang=en&supportedLangs=en-US%2Cen-US%2Cen-US%2Cen&purpose={purpose}&token={captcha_token}", headers=headers)
			data = r.json()
			token, contest_id, n_leading_zeros, challenges = data["token"], data["contestId"], data["nLeadingZerosRequired"], data["challenges"]
			
			challenge_id = f"{captcha_token}:{k}{token}"
			background_img = (await client.get(f"https://verify-api.proton.me/captcha/v1/api/bg?token={token}", headers=headers)).content 
			puzzle_img = (await client.get(f"https://verify-api.proton.me/captcha/v1/api/puzzle?token={token}", headers=headers)).content 
			
			solution = self.generate_solution_coodinates(puzzle_img, background_img)
			x, y = random.randint(20, 54), random.randint(11, 54)
			button = []
			
			#coordinates from a random point on the captcha to the puzzle
			crds_part1 = self.hc.generate_path([random.randint(80, 370), random.randint(150, 400)], [x, y])
			button.extend([0] * len(crds_part1))

			# mouse coordinates from the puzzle to the puzzle solution coordinates
			crds_part2 = self.hc.generate_path([x, y], [solution[0], solution[1]])
			button.extend([1] * len(crds_part2))

			# coordinates from the puzzle to next button
			crds_part3 = self.hc.generate_path([solution[0], solution[1]], [random.randint(10, 360), random.randint(408, 440)])
			button.extend(([0] * (len(crds_part3) - 4)) + ([1] * 4))

			timestamps = self.generate_timestamps(len(crds_part1) + len(crds_part2) + len(crds_part3))
			x, y =  zip(*(crds_part1 + crds_part2 + crds_part3))

			client_data = self.generate_client_data(x, y, button, timestamps)

			piece_load = random.randint(200, 380) + random.uniform(-1e-10, 1e-10)
			bg_load = piece_load + random.randint(5, 20) + random.uniform(-1e-10, 1e-10)
			challenge_load = bg_load + random.randint(5, 20) + random.uniform(-1e-10, 1e-10)
			answers, elapsed = self.solve_pow(challenges, n_leading_zeros)
			pcaptcha = {
				"x":solution[0],
				"y":solution[1],
				"answers": answers,
				"clientData": client_data,
				"pieceLoadElapsedMs":piece_load,
				"bgLoadElapsedMs":bg_load,
				"challengeLoadElapsedMs":challenge_load,
				"solveChallengeMs":timestamps[-1],
				"powElapsedMs":timestamps[-1] + elapsed
			}
			headers["pcaptcha"] = json.dumps(pcaptcha).replace(" ", "")
			r = await client.get(f"https://verify-api.proton.me/captcha/v1/api/validate?token={token}&contestId={contest_id}&purpose={purpose}", headers=headers)
			if r.status_code == 200:
				del headers["pcaptcha"]
				r = await client.get(f"https://verify-api.proton.me/captcha/v1/api/finalize?contestId={contest_id}&purpose={purpose}", headers=headers)
				return challenge_id
			return None

	def generate_timestamps(self, count):
		timestamps = []
		current = float(random.randint(1000, 3000))
		start = random.randint(1000, 2800)
		for _ in range(count):
			step = random.uniform(0.5, 3.0)
			current += step
			timestamps.append(current + random.uniform(-0.0001, 0.0001))
		return timestamps

	def generate_solution_coodinates(self, puzzle_img, background_img):
		puzzle_piece = cv2.imdecode(np.frombuffer(puzzle_img, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
		background = cv2.imdecode(np.frombuffer(background_img, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)

		blur_background = cv2.GaussianBlur(background, (3, 3), 0)
		edges_background = cv2.Canny(blur_background, 50, 150)

		_, thresh = cv2.threshold(puzzle_piece, 30, 255, cv2.THRESH_BINARY)

		mask = np.zeros_like(thresh)
		contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		cv2.drawContours(mask, contours, -1, color=255, thickness=1)

		result = cv2.matchTemplate(edges_background, mask, cv2.TM_CCOEFF_NORMED)
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

		#uncomment to view solution location
		# h, w = mask.shape
		# matched = cv2.cvtColor(background, cv2.COLOR_GRAY2BGR)
		# cv2.rectangle(matched, max_loc, (max_loc[0]+w, max_loc[1]+h), (0,255,0), 2)
		# cv2.imshow('Matched', matched)
		# cv2.waitKey(0)
		# cv2.destroyAllWindows()
		
		return max_loc

	def compress_array(self, e):
		if len(e) == 0:
			return [0]

		result = []
		repetition_counter = 1
		last_value = e[0]
		literal_values = [last_value]

		for current_value in e[1:]:
			if current_value == last_value:
				if len(literal_values) > 1:
					literal_values.pop()
					result.append(-len(literal_values))
					result.extend(literal_values)
					literal_values = []
				repetition_counter += 1
			
			else:
				if repetition_counter > 1:
					result.extend([repetition_counter, last_value])
					repetition_counter = 1
					literal_values = [current_value]
				else:
					literal_values.append(current_value)
				last_value = current_value
		
		if len(literal_values) > 1:
			result.append(-len(literal_values))
			result.extend(literal_values)

		elif repetition_counter >= 1:
			result.extend([repetition_counter, last_value])

		result.append(0)
		return result

	def generate_client_data(self, x, y, button, timestamps):
		s = self.compress_array(x) + self.compress_array(y) + self.compress_array(button) + self.compress_array(timestamps)
		a = np.array(s, dtype=np.int16)
		o = a.view(dtype=np.uint8)
		l = bytearray(zlib.compress(o))
		if len(l) > 1:
			l[0] ^= 150
			l[1] ^= 181
		return base64.b64encode(l).decode("utf-8")

	def solve_pow(self, challenges, n_leading_zeros):
		start = time.perf_counter()
		answers = []
		for e in challenges:
			a = 0
			while True:
				f = hashlib.sha256(f"{a}{e}".encode("utf-8")).hexdigest()
				g = math.ceil(n_leading_zeros / 4)
				h = f[:g]
				i = int("0x" + h, 16)
				if (i < math.pow(2, 4 * g - n_leading_zeros)):
					answers.append(a)
					break
				a += 1
		end = time.perf_counter()
		elapsed = (end - start) * 1000
		return answers, elapsed

if __name__ == "__main__":
	k = protonSolver()
	p = asyncio.run(k.solve_challenge("QtdNFs9M1gaYdfzPtEKiJ61f"))
	print(f"solution={p}")
