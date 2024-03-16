"""Module for scraping xiaobaotv.app"""

import json
import click
import requests
from bs4 import BeautifulSoup
import yt_dlp


@click.command()
@click.option(
    "--file", prompt="File name", help="The file to be read", default="urls.txt"
)
def scrape(file):
    # read each line of the file as a url
    with open(file, "r", encoding="utf-8") as f:
        urls = f.readlines()

    # make sure each url is a www.xiaobaotv.app url, throw error if not
    for url in urls:
        if "www.xiaobaotv.app" not in url:
            raise ValueError(f"{url} is not a valid xiaobaotv.app url")

    # skip commented out urls
    urls = [url for url in urls if not url.startswith("#")]

    # download each url
    for url in urls:
        click.echo(f"Downloading {url}")

        # check if the url has been scraped before, if so, skip
        try:
            with open("progress.txt", "r", encoding="utf-8") as f:
                if url in f.read():
                    click.echo(f"{url} has been scraped before, skipping...")
                    continue
        except FileNotFoundError:
            pass

        # download the page with a timeout of 10 seconds
        response = requests.get(url, timeout=10)

        # parse the page
        soup = BeautifulSoup(response.text, "html.parser")

        # find video name from now playing text `正在播放：...`
        # <div class="tips close-box" style="background-color: #181515">
        #   <a class="tips-close-btn pull-right" href="javascript:;"
        #     ><i class="fa fa-close"></i
        #   ></a>
        #   <ul>
        #     <li>正在播放：繁花（沪语版）-2</li>
        #     <li>
        #       <i class="fa fa-volume-down"></i
        #       >请勿轻易相信视频中的任何广告，谨防上当受骗
        #     </li>
        #     <li>小宝影院最新官方域名：xiaobaotv.app</li>
        #   </ul>
        # </div>
        div = soup.find("div", class_="tips close-box")
        video_name = div.find("li").text.split("：")[1]

        # find a div with class `embed-responsive clearfix`
        div = soup.find("div", class_="embed-responsive clearfix")
        script = div.find("script")
        # print(script.text)

        # parse var player_aaaa = { ... } using json
        player = json.loads(script.text.split("=")[1].strip().replace(";", ""))
        print(player)

        # get 'url' from player
        m3u_url = player["url"]

        # download the m3u file with yt-dlp, and embed the video name into the metadata
        ydl_opts = {
            "outtmpl": f"{video_name}.mp4",
            "addmetadata": True,
            "metadatafromtitle": video_name,
            "fragment-retries": "infinite",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([m3u_url])

        # write progress to file
        with open("progress.txt", "a", encoding="utf-8") as f:
            f.write(url)


if __name__ == "__main__":
    scrape()  # pylint: disable=no-value-for-parameter
