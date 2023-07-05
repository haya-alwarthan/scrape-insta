import scrapy
import urllib
import json
from datetime import datetime

from img2text.img_to_text import convert_img_to_text


class InstagramAccount(scrapy.Spider):
    name = 'InstagramAccount'
    allowed_domains = ['api.webscraping.ai']
    count = 0

    # starting with the profile page with first page of posts data
    def start_requests(self):
        for username in self.usernames.split(","):
            print("hi im in start, username = {}".format(username))
            profile_url = f"https://www.instagram.com/{username}/?__a=1"
            yield self.api_request(profile_url, self.parse_account_page)

    # wrapping the URL in a api.webscraping.ai API request to avoid login
    def api_request(self, target_url, parse_callback, meta=None):
        self.count += 1
        # print('Requesting: %s', target_url)
        api_params = {'api_key': self.api_key, 'proxy': 'residential', 'timeout': 20000, 'url': target_url}
        # print(" im in api_request, params = {}".format(api_params))
        api_url = f"https://api.webscraping.ai/html?{urllib.parse.urlencode(api_params)}"
        print("count {}".format(self.count))
        return scrapy.Request(api_url, callback=parse_callback, meta=meta)

    # posts GraphQL pagination requests
    def graphql_posts_request(self, user_id, end_cursor):
        graphql_variables = {'id': user_id, 'first': 12, 'after': end_cursor}
        # query_hash is a constant for this type of query
        # print("graph variables {}".format(graphql_variables))
        graphql_params = {'query_hash': 'e769aa130647d2354c40ea6a439bfc08', 'variables': json.dumps(graphql_variables)}
        url = f"https://www.instagram.com/graphql/query/?{urllib.parse.urlencode(graphql_params)}"
        return self.api_request(url, self.parse_graphql_posts, meta={'user_id': user_id})

    # parsing the initial profile page
    def parse_account_page(self, response):
        print('callback: parse_account_page...')
        all_data = json.loads(response.text)
        # self.logger.info('Parsing account data: %s', all_data)
        user_data = all_data['graphql']['user']

        for post_data in user_data['edge_owner_to_timeline_media']['edges']:
            # multiple media will be returned in case of a carousel
            for parsed_post in self.parse_post(post_data):
                yield parsed_post

        if user_data['edge_owner_to_timeline_media']['page_info']['has_next_page']:
            print("there is a next page")
            end_cursor = user_data['edge_owner_to_timeline_media']['page_info']['end_cursor']
            user_id = user_data['id']
            yield self.graphql_posts_request(user_id, end_cursor)

    # parsing the paginated posts
    def parse_graphql_posts(self, response):
        self.logger.info('callback Parsing GraphQL response...')
        posts_data = json.loads(response.text)
        # print('Parsing GraphQL data: %s', posts_data)
        timeline_media = posts_data['data']['user']['edge_owner_to_timeline_media']

        for post in timeline_media['edges']:
            # multiple media will be returned in case of a carousel
            for parsed_post in self.parse_post(post):
                yield parsed_post

        if timeline_media['page_info']['has_next_page']:
            user_id = response.meta['user_id']
            end_cursor = timeline_media['page_info']['end_cursor']
            yield self.graphql_posts_request(user_id, end_cursor)

    # extracting the post information from JSON
    def parse_post(self, post_data):
        # self.logger.info('Parsing post data: %s', post_data)
        post_data = post_data['node']
        print("im in posts")

        base_post = {
            'username': post_data['owner']['username'],
            'user_id': post_data['owner']['id'],
            'post_id': post_data['id'],
            'is_video': post_data['is_video'],
            'media_url': post_data['video_url'] if post_data['is_video'] else post_data['display_url'],
            'like_count': post_data['edge_media_preview_like']['count'],
            'comment_count': post_data['edge_media_to_comment']['count'],
            'caption': post_data['edge_media_to_caption']['edges'][0]['node']['text'] if
            post_data['edge_media_to_caption']['edges'] else None,
            'location': post_data['location']['name'] if post_data['location'] else None,
            'timestamp': post_data['taken_at_timestamp'],
            'date_posted': datetime.fromtimestamp(post_data['taken_at_timestamp']).strftime("%d-%m-%Y %H:%M:%S"),
            'post_url': f"https://www.instagram.com/p/{post_data['shortcode']}/",
            'thumbnail_url': post_data['thumbnail_resources'][-1]['src'],
        }

        try:
            text = ''
            print('search term== {}'.format(self.term))
            img_path_frontend = f"frontend/src/assets/temp/images/{base_post['post_id']}.jpeg"
            img_path = f"static/images/{base_post['post_id']}.jpeg"
            urllib.request.urlretrieve(base_post['thumbnail_url'], img_path_frontend)
            text += convert_img_to_text(img_path_frontend)
            # print("extracted text {}".format(text))

        except Exception as error:
            print("not found :{}".format(error))
            text = "not found"
        try:
            base_post['media_text'] = text
            if base_post['caption'] is None:
                base_post['caption'] = ''
            # TODO: find a way to add the post's comments within the searched space (probably through graphGl )
            searched_space = base_post['media_text'] + ' ' + base_post['caption']
            posts = []

            if self.term in searched_space:
                posts = [base_post]
            else:
                print("elseeeeeee")
                # adding secondary media for carousels with multiple photos
                if "edge_sidecar_to_children" in post_data:
                    for carousel_item in post_data["edge_sidecar_to_children"]["edges"]:
                        carousel_post = {
                            **base_post,
                            'post_id': carousel_item['node']['id'],
                            'thumbnail_url': carousel_item['node']['display_url'],
                            'media_url': carousel_item['node']['display_url'],
                        }

                        img_path_frontend = f"frontend/src/assets/temp/images/{carousel_post['post_id']}.png"
                        img_path = f"static/images/{carousel_post['post_id']}.png"
                        urllib.request.urlretrieve(carousel_post['thumbnail_url'], img_path_frontend)
                        text += convert_img_to_text(img_path_frontend)
                        searched_space = carousel_post['media_text'] + ' ' + carousel_post['caption']
                        posts = []
                        if self.term in searched_space:
                            posts.append(carousel_post)

        except Exception as e:
            print("errorrrrrr :{}".format(e))
        print("posts ========={}".format(posts))

        return posts
