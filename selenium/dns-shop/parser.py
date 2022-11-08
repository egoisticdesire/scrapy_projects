import json
import os
import pickle
import re

from time import sleep
from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


def check_cookies(driver, current_city):
    path_to_cookie = f'cookies/{current_city}'

    if not os.path.exists('cookies/'):
        os.mkdir('cookies/')

    if os.path.exists(path_to_cookie):
        for cookie in pickle.load(open(path_to_cookie, 'rb')):
            driver.add_cookie(cookie)
        sleep(1)
        driver.refresh()
        print('Cookies applied!')
        sleep(5)
    else:
        city_name = driver.find_element(
            by=By.CLASS_NAME,
            value='city-select__text',
        )
        if city_name != current_city:
            city_name.click()
            sleep(5)

            change_city = driver.find_element(
                by=By.CLASS_NAME,
                value='base-ui-input-search__input_YOW',
            )
            change_city.send_keys(current_city)
            sleep(1)
            change_city.send_keys(Keys.ENTER)
            sleep(5)

        pickle.dump(driver.get_cookies(), open(path_to_cookie, 'wb'))
        print('New Cookies saved!')


def get_data(url, change_city_name='Москва'):
    # Enabling options
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={UserAgent().chrome}')
    # Disabling webdriver detection
    options.add_argument('--disable-blink-features=AutomationControlled')
    # Enabling Silent mode
    # options.add_argument('--headless')

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
        driver.get(url=url)
        sleep(5)

        # Checking Cookies
        check_cookies(driver=driver, current_city=change_city_name)

        # Detecting Category of products
        category = driver.find_element(
            by=By.CLASS_NAME,
            value='breadcrumb_last',
        ).find_element(
            by=By.TAG_NAME,
            value='span',
        ).text.strip()

        # REGEX = r'(?<=[а-яА-ЯёЁ]\s)[a-zA-Z]+(?=\s)'
        # brands = set()

        data_results = []

        try:
            # Checking pagination
            last_page = driver.find_element(
                by=By.CLASS_NAME,
                value='pagination-widget__page-link_last'
            ).get_attribute('href').split('=')[-1]

            while range(int(last_page) - 1):
                next_page_url = driver.find_element(
                    by=By.CLASS_NAME,
                    value='pagination-widget__show-more-btn'
                )
                sleep(1)
                next_page_url.click()
                sleep(3)

        except NoSuchElementException:
            pass
        finally:
            try:
                # Getting data
                products_list = driver.find_elements(
                    by=By.CLASS_NAME,
                    value="catalog-product",
                )
                print(f'{len(products_list)} products found...')
                sleep(1)

                for item in products_list:
                    item_text = item.find_element(
                        by=By.CLASS_NAME,
                        value="catalog-product__name",
                    ).text.strip()

                    # brands.add(re.search(REGEX, item_text).group())

                    item_link = item.find_element(
                        by=By.LINK_TEXT,
                        value=item_text,
                    ).get_attribute('href').strip()

                    try:
                        # Checking the availability of product
                        item_available = item.find_element(
                            by=By.CLASS_NAME,
                            value='order-avail-wrap__link',
                        ).get_attribute('data-mobile-text').strip()

                        item_price = item.find_element(
                            by=By.CLASS_NAME,
                            value='product-buy__price',
                        ).text.strip().split('\n')

                    except NoSuchElementException:
                        item_available = 'The product is out of stock'
                        item_price = (item_available, )

                    data_results.append(
                        {
                            'title': item_text,
                            'url': item_link,
                            'available': item_available,
                            'price': item_price[0],
                            'old_price': f'{item_price[1]} ₽' if len(item_price) > 1 else 'No discounts',
                        }
                    )

            except NoSuchElementException:
                pass
            finally:
                print(f'{len(data_results)} titles recorded.')

                if not os.path.exists(f'data/{change_city_name}/'):
                    os.mkdir(f'data/{change_city_name}/')

                path = f'data/{change_city_name}/{category}.json'

                with open(path, 'w', encoding='utf-8') as file:
                    json.dump(data_results, file, indent=4, ensure_ascii=False)

                print(f'Enjoy! Data saving path: {path}')

    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()


def main():
    url = 'https://www.dns-shop.ru/catalog/17a89aab16404e77/videokarty/?stock=now-today-tomorrow-later-out_of_stock&brand=afox-kfa2&f[mv]=1dn4f0-udtje-13n3m1-udtf8-145iin-uiykt'
    get_data(url=url)


if __name__ == '__main__':
    main()
