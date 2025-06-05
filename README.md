# Proton Mail Puzzle CAPTCHA Solver

Async Python-based solver for the Proton Mail 2D puzzle CAPTCHA, designed for educational purposes.

![Proton](https://github.com/user-attachments/assets/83171198-ad58-43e0-b455-d62dd459c120)

## Features

- Automatically solves a Proton mail CAPTCHA challenge.
- Uses OpenCV to identify puzzle pieces.
- Generates realistic human cursor movment to evade detection.
- Fully requests based.

## Usage
```python
import asyncio
from captcha_solver import protonSolver

captcha_token = ""
proxy = ""
async def main():
  k = protonSolver()
  solution = await k.solve_challenge(captcha_token, proxy)
  
asyncio.run(main())
```
## Notes
In order to fetch the challenge and the captcha to be displayed, a valid captcha_token must be supplied to the solver, this token can be obtained when creating an account or logging in, supplying a non valid token causes captcha to not load when visiting
"https://verify-api.proton.me/core/v4/captcha?Token=captcha_token_here&ForceWebMessaging=1&Dark=true"

To speed up development i made a mitmproxy addon (mitmproxy_addon.py) that always loads the captcha regardless if the token is valid or not.

## Acknowledgements
[HumanCursor](https://github.com/riflosnake/HumanCursor)
