<div align="center">
  <h1>🎓 UT-FineArts Registration Bot</h1>
  <p>A professional, highly-customizable Telegram Bot built for managing university event registrations, ticketing, and dynamic workshop reservations.</p>
</div>

<hr>

## 🌟 Features

* **Dynamic Workshop Management:** Admins can create, open, and close workshops directly from the bot.
* **Collision Detection:** Prevents users from registering for multiple workshops in overlapping time slots.
* **Smart Capacity & Backup Lists:** Automatically manages workshop capacities and routes overflowing participants to a "Reserve List" without dropping them.
* **Total Event Capacity:** Ability to cap the entire event registration and automatically pause signups.
* **Tiered Pricing:** Update ticket prices on the fly for Early Bird, Normal, and Late registration tiers.
* **Admin Dashboard:** In-chat interactive dashboard with live stats, Excel exports (`.xlsx`), and massive broadcast messaging.
* **Automated Ticketing:** Auto-generates unique QR code tickets for approved users.
* **Persian Support:** Built-in smart conversion of Persian & Arabic digits (`۱۲۳`) to English digits (`123`).

## 🚀 Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/khodekia/UT-FineArts.git
   cd UT-FineArts
   ```

2. **Install dependencies**
   Make sure you have Python 3.10+ installed.
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Rename `.env.example` to `.env` and fill in your details:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_CHANNEL_ID=-100123456789
   CARD_NUMBER=1234-5678-1234-5678
   CARD_HOLDER=Your Name
   ADMIN_USER_IDS=11111111,22222222
   SUPPORT_ID=@YourSupportID
   ```

4. **Run the bot**
   ```bash
   python3 main.py
   ```

## 🛠️ Usage

* **Users:** Send `/start` to begin the registration flow.
* **Admins:** Send `/admin` to open the secure admin control panel.

---

## 💖 Open Source & Donations

Feel free to use, fork, modify, and host this bot for your own events! It's completely fine to use this codebase for your communities. 

If this bot saved you time, made your event run smoother, or you just appreciate the work, please consider leaving a donation! It helps keep the coffee flowing and the servers running. ☕

* **Bitcoin (BTC):** `bc1q...your_btc_address_here`
* **Ethereum (ETH):** `0x...your_eth_address_here`
* **Dogecoin (DOGE):** `D...your_doge_address_here`
* **USDC (ERC-20/Polygon):** `0x...your_usdc_address_here`

*(Note: Replace the placeholder addresses above with your actual crypto wallet addresses).*

---
<div align="center">
  <i>Developed with ❤️ for the University of Tehran Fine Arts community.</i>
</div>
