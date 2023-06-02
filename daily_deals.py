#!/usr/bin/env python3
import requests
import html
import json
from types import NoneType
from typing import Literal, LiteralString, Sequence
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from bs4.element import PageElement, ResultSet


@dataclass
class Deal:
    id: int
    title: LiteralString
    original_price: float
    current_price: float
    seller: LiteralString
    path: Path
    available: bool

    def __repr__(self) -> str:
        return f'''Deal(
    id={self.id},
    title={self.id},
    original_price={self.original_price},
    current_price={self.current_price},
    seller={self.seller},
    path={self.path},
    available={self.available},
        )'''

    @classmethod
    def from_json(cls, data: dict):
        if not isinstance(data, dict):
            raise TypeError('Must instantiate from dict type')
        
        return cls(
            id=data['id'],
            title=data['title'],
            original_price=float(data['variants'][0]['compare_at_price']) / 100 
                if not isinstance(data['variants'][0]['compare_at_price'], NoneType) 
                else None,
            current_price=float(data['variants'][0]['price']) / 100
                if not isinstance(data['variants'][0]['price'], NoneType) 
                else None,
            seller=data['vendor'],
            path=Path(html.unescape(data['url'])),
            available=True if data['available'] else False
        )


    @property
    def savings_amount(self):
        return self.original_price - self.current_price
    
    @property
    def savings_percentage(self):
        return self.current_price / self.original_price


@dataclass
class DailyDeals:
    updated_date: datetime
    expiry_date: datetime
    deals: Sequence[Deal]
    

    @property
    def is_empty(self):
        return len(self.deals) == 0



class BJJFanaticsScraper:

    BASE_URL = 'https://bjjfanatics.com/collections/daily-deals'

    
    @classmethod
    def get_deals(cls) -> DailyDeals:
        return cls._list_deals()
        
    @classmethod
    def _list_deals(cls) -> DailyDeals:
        cards = cls._request_cards()
        deals_data = cls._parse_deals(cards)
        deals_info = cls._get_deals_info()
        deals = DailyDeals(
            updated_date=datetime.fromisoformat(deals_info['updated_at']),
            expiry_date=datetime.fromisoformat(deals_info['updated_at']) + timedelta(days=1),
            deals=deals_data
        )
        return deals
    
    @classmethod
    def _get_deals_info(cls) -> dict:
        res = requests.get(
            url=BJJFanaticsScraper.BASE_URL + '.json',
            headers={'Accept': 'application/json'}
            )
        data = json.loads(res.content)
        return data['collection']
        

    @classmethod
    def _request_cards(cls) -> Sequence[PageElement]:
        headers = {'Accept-Encoding': 'identity'}
        params = {'page': 1}
        
        res = requests.get(
            url=BJJFanaticsScraper.BASE_URL,
            params=params,
            headers=headers
        )

        if res.status_code != requests.codes.ok:
            raise requests.exceptions.RequestException(res)
        
        soup = BeautifulSoup(html.unescape(res.text), 'html.parser')
        
        with open('example.html', 'w', encoding="utf-8") as f:
            f.write(res.text)

        cards: Sequence[PageElement] = soup.find_all(
            name='script',
            attrs={'class':'bc-sf-filter-product-script'}
        )


        return cards
    

    @staticmethod
    def _parse_deals(cards: Sequence[PageElement]) -> Sequence[Deal]:
        if not isinstance(cards, Sequence):
            raise TypeError('Can only parse a Sequence containing PageElements.')
        return [Deal.from_json(json.loads(card.get_text())) for card in cards if '"compare_at_price_min": 0,' not in card.get_text()]



if __name__ == '__main__':
    d = BJJFanaticsScraper.get_deals()
    print(d.date)

