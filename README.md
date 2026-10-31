# r/pokemongo RSS feed

This repository republishes new posts from [Reddit's r/pokemongo feed](https://www.reddit.com/r/pokemongo/.rss) as RSS 2.0.

## Subscribe

https://raw.githubusercontent.com/Pretendworking/r_pokemongo/main/feed.xml

GitHub Actions checks for new posts every five minutes. GitHub may delay scheduled runs during periods of high load, so the refresh interval is not guaranteed. You can also run the **Update Reddit RSS feed** workflow manually from the repository's **Actions** tab.

The feed includes up to 100 entries supplied by Reddit. If Reddit rate limits or temporarily rejects a request, the workflow fails and the last successfully generated feed remains available.
