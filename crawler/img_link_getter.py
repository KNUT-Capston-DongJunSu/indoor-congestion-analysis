from .img_links_crawler import ImgLinksCrawlerService

if __name__ == "__main__":
    service = ImgLinksCrawlerService()
    service.start_crawler("https://map.naver.com/p/entry/place/1094965330?placePath=/photo", False)