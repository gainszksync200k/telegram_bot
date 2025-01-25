
import asyncio
import logging
from telegram import Bot
from aiohttp import ClientSession


# Ваш API токен
TOKEN = "YOUR_BOT_API" # УКАЖИТЕ СЮДА АПИ ПОЛУЧЕНЫЙ В ШАГЕ 2.

# Ваш собственный ID пользователя
SELF_CHAT_ID = "YOUR_ID_TELEGRAM" # УКАЖИТЕ СЮДА ID ПОЛУЧЕНЫЙ В ШАГЕ 3.

# ЧАСТОТА ОТПРАВЛЕНИЙ СООБЩЕНИЯ, В МИНУТАХ
TIME = 5 # Я СДЕЛАЛ 5 МИНУТ, МОЖНО РЕЖЕ, НО НЕ МЕНЬШЕ 5 МИНУТ, А ТО ВАШ АПИ ЗАБАНЯТ ЗА ЧАСТЫЕ ЗАПРОСЫ!!!!

# ТОКЕНЫ И ИХ КОЛИЧЕСТВО ДЛЯ ПОЛУЧЕНИЯ ВАШЕГО ОБЩЕГО БАЛАНСА ПОРТФЕЛЯ.
# НУЖНО ЗАПОЛНИТЬ ПО ПРИМЕРУ НИЖЕ. ПОЛУЧИТЬ ВЕРНЫЙ ТИКЕТ МОЖНО ТУТ https://www.coingecko.com/en/coins/shiba-inu
# В ДАННОМ СЛУЧАЕ ДЛЯ ШИБЫ ЭТО БУДЕТ  shiba-inu .  ДЛЯ ЭФИРА ethereum
# ПОСЛЕ ДВОЕТОЧИЯ СУММА ВАШЕГО АКТИВА
tokens = {
    "ethereum": 20.54,  # ETH , ЕГО КОЛИЧЕСТВО
    "internet-computer": 1231,  # ICP
    "chainlink": 348,  # LINK
    "filecoin": 1506,  # FIL
    "sushi": 4294,  # SUSHI
    "flow": 5358,  # FLOW
    "polkadot": 404,  # DOT
    "the-graph": 522  # GRT
}

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Формат сообщений
    handlers=[
        logging.FileHandler("bot.log"),  # Логирование в файл
        logging.StreamHandler()  # Логирование в консоль
    ]
)
logger = logging.getLogger(__name__)


async def get_prices():
    prices = []
    logger.info("Запуск функции get_prices для получения данных о ценах.")

    async with ClientSession() as session:
        # Запрос цены ETH
        async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd") as response:
            if response.status == 200:
                data = await response.json()
                prices.append(data["ethereum"]["usd"])
                logger.info(f"Цена ETH получена: {data['ethereum']['usd']} USD")
            else:
                logger.error(f"Ошибка при запросе цены ETH: {response.status}")

        # Запрос цены BTC
        async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd") as response:
            if response.status == 200:
                data = await response.json()
                prices.append(data["bitcoin"]["usd"])
                logger.info(f"Цена BTC получена: {data['bitcoin']['usd']} USD")
            else:
                logger.error(f"Ошибка при запросе цены BTC: {response.status}")

        # Запрос цены USDT в рублях
        async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=rub") as response:
            if response.status == 200:
                data = await response.json()
                prices.append(data["tether"]["rub"])
                logger.info(f"Цена USDT получена: {data['tether']['rub']} RUB")
            else:
                logger.error(f"Ошибка при запросе цены USDT: {response.status}")

        # Запрос индекса страха и жадности
        async with session.get("https://api.alternative.me/fng/?limit=1") as response:
            if response.status == 200:
                data = await response.json()
                fear_greed_index = data['data'][0]['value']
                fear_greed_classification = data['data'][0]['value_classification']
                prices.append(fear_greed_index)
                prices.append(fear_greed_classification)
                logger.info(f"Индекс страха и жадности получен: {fear_greed_index} ({fear_greed_classification})")
            else:
                logger.error(f"Ошибка при запросе индекса страха и жадности: {response.status}")

        # Запрос GAS PRICE
        api_key = "YC33Z9NA3RKC4WRT3JA3A2M7KZTEHTEBMV"
        async with session.get(f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={api_key}") as response:
            if response.status == 200:
                data = await response.json()
                propose_gas_price = data['result']['ProposeGasPrice']
                prices.append(propose_gas_price)
                logger.info(f"GAS PRICE получен: {propose_gas_price}")
            else:
                logger.error(f"Ошибка при запросе GAS PRICE: {response.status}")

        # Запрос индекса доминации битка
        async with session.get("https://api.coingecko.com/api/v3/global") as response:
            if response.status == 200:
                data = await response.json()
                bitcoin_dominance = data["data"]["market_cap_percentage"]["btc"]
                prices.append(bitcoin_dominance)
                logger.info(f"Доминация BTC получена: {bitcoin_dominance:.2f}%")
            else:
                logger.error(f"Ошибка при запросе доминации BTC: {response.status}")

    return prices


async def portfolio():
    logger.info("Запуск функции portfolio для расчета стоимости портфеля.")

    async def get_crypto_prices(coin_ids):
        async with ClientSession() as session:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": ",".join(coin_ids),  # Передаем список ID криптовалют
                "vs_currencies": "usd"  # Получаем цены в USD
            }
            async with session.get(url=url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Ошибка при запросе цен криптовалют: {response.status}")
                    raise Exception(f"Ошибка при запросе к API: {response.status}")

    # Портфель: словарь с названием криптовалюты и её количеством
    portfolio = tokens

    # Получаем текущие цены для криптовалют в портфеле
    prices = await get_crypto_prices(portfolio.keys())

    # Рассчитываем общую стоимость портфеля
    total_value = 0
    for asset, amount in portfolio.items():
        if asset in prices:
            asset_value = prices[asset]["usd"] * amount
            total_value += asset_value
            logger.info(f"{asset.capitalize()}: {amount} шт. = ${asset_value:.2f}")
        else:
            logger.warning(f"Криптовалюта {asset} не найдена в API.")

    logger.info(f"Общая стоимость портфеля: ${total_value:.2f}")
    return total_value


# ОТПРАВКА СООБЩЕНИЯ В БОТ
async def send_message(bot, chat_id, message):
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        logger.info("Сообщение успешно отправлено.")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")

# ОСНОВНАЯ ЛОГИКА СКРИПТА
async def main():
    logger.info("Запуск основной функции main.")
    prices = await get_prices()
    portfolio_value = await portfolio()
    message = (
        f"ЦЕНА ETH: {prices[0]:.2f} USD\n\n"
        f"ЦЕНА BTC: {prices[1]:.2f} USD\n\n"
        f"ЦЕНА USDT: +-{prices[2] + 1.6:.2f} RUB\n\n"
        f"Значение страха {prices[3]} и уровень страха {prices[4]}\n\n"
        f"GAS PRICE = {prices[5]}\n\n"
        f"Доминация BTC {prices[6]:.2f}\n\n"
        f"Стоимость портфеля: ${portfolio_value:.2f}"
    )

    bot = Bot(token=TOKEN)
    await send_message(bot, SELF_CHAT_ID, message)

# ЗАПУСК ОСНОВНОЙ ЛОГИКЕ В БЕСКОНЕЧНОМ ЦИКЛЕ С ЗАДЕРЖКОЙ ОТПРАВКИ СООБЩЕНИЙ
async def bot_start():
    logger.info("Бот запущен.")
    while True:
        await main()
        logger.info("Ожидание 5 минут перед следующим запуском.")
        await asyncio.sleep(60 * TIME)  # Ожидание 5 минут


# ЗАПУСК СКРИПТА
try:
    asyncio.run(bot_start())
except Exception as e:
    logger.critical(f"Критическая ошибка: {e}")
