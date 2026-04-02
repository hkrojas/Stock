import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional

class ScraperService:
    @staticmethod
    async def get_product_details(url: str) -> Dict[str, Any]:
        """
        Extracts product details from a given URL.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
            try:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
            except Exception as e:
                return {"error": f"Error al acceder a la URL: {str(e)}"}
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Detect handler
            if "sodimac.com" in url:
                return ScraperService._handle_sodimac(soup, url)
            elif "promart.pe" in url:
                return ScraperService._handle_promart(soup, url)
            else:
                return ScraperService._handle_generic(soup, url)

    @staticmethod
    def _handle_sodimac(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {"source": "Sodimac", "url": url}
        
        # Name
        name_tag = soup.find("h1", class_="product-title")
        data["name"] = name_tag.get_text(strip=True) if name_tag else "Producto Sodimac"
        
        # Price
        price_tag = soup.find("div", class_="price")
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            match = re.search(r"(\d+\.?\d*)", price_text.replace(",", ""))
            data["price"] = float(match.group(1)) if match else 0.0
        else:
            data["price"] = 0.0
            
        # Image
        img_tag = soup.find("img", class_="product-image")
        if img_tag and img_tag.get("src"):
            data["image_url"] = img_tag["src"]
        else:
            # Fallback to OG tags
            og_img = soup.find("meta", property="og:image")
            data["image_url"] = og_img["content"] if og_img else None
            
        # Description
        desc_tag = soup.find("div", class_="product-description")
        data["description"] = desc_tag.get_text(strip=True) if desc_tag else ""
        
        return data

    @staticmethod
    def _handle_promart(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {"source": "Promart", "url": url}
        
        # Name
        name_tag = soup.find("h1", class_="vtex-store-components-3-x-productNameContainer")
        data["name"] = name_tag.get_text(strip=True) if name_tag else "Producto Promart"
        
        # Price
        price_tag = soup.find("span", class_="vtex-product-price-1-x-currencyInteger")
        if price_tag:
            data["price"] = float(price_tag.get_text(strip=True).replace(",", ""))
        else:
            data["price"] = 0.0
            
        # Image
        og_img = soup.find("meta", property="og:image")
        data["image_url"] = og_img["content"] if og_img else None
            
        # Description
        desc_tag = soup.find("div", class_="vtex-store-components-3-x-productDescriptionText")
        data["description"] = desc_tag.get_text(strip=True) if desc_tag else ""
        
        return data

    @staticmethod
    def _handle_generic(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {"source": "Generic", "url": url}
        
        # Meta OG Tags are best for generic
        og_title = soup.find("meta", property="og:title")
        data["name"] = og_title["content"] if og_title else soup.title.string if soup.title else "Producto Genérico"
        
        og_img = soup.find("meta", property="og:image")
        data["image_url"] = og_img["content"] if og_img else None
        
        og_desc = soup.find("meta", property="og:description")
        data["description"] = og_desc["content"] if og_desc else ""
        
        data["price"] = 0.0 # Hard to guess generic price
        
        return data
