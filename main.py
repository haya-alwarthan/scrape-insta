import json

import crochet

crochet.setup()
from gevent import monkey

monkey.patch_all()
from gevent.pywsgi import WSGIServer
from flask import Flask, render_template, jsonify, request, redirect, url_for, stream_with_context, Response, send_file
from scrapy import signals
from scrapy.crawler import CrawlerRunner
from scrapy.signalmanager import dispatcher
import time
from flask_cors import CORS
import os
import glob

# Importing our Scraping Function from the InstagramAccount file

from insta_spider.insta_spider.spiders.InstagramAccount import InstagramAccount

from img2text.img_to_text import convert_img_to_text

app = Flask(__name__)
# cors = CORS(app, resources={r"/submit": {"origins": "http://localhost:4200"}})
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
output_data = []
data_list = []
searchTerm = ''
account = ''
counter = 0
crawl_runner = CrawlerRunner()
scrape_in_progress = False
scrape_complete = False
custom_settings = {'FEED_URI': 'output.json',
                   }  # This will tell scrapy to store the scraped data to outputfile.json and for how long the spider should run.
crawl_runner.settings = custom_settings


# By Default Flask will come into this when we run the file
@app.route('/')
def index():
    return render_template("index.html")  # Returns index.html file in templates folder.


# @app.after_request
# def after_request(response):
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
#     return response


# After clicking the Submit Button FLASK will come into this
@app.route('/submit', methods=['POST'])
def submit():
    # print("hello im in submit root, request:  {}".format(request.json))
    if request.method == 'POST':
        global searchTerm
        global account
        account = request.json['account']  # Getting the Input Amazon Product URL
        searchTerm = request.json['search_term']

        # This will remove any existing file with the same name so that the scrapy will not append the data to any previous file.
        if os.path.exists("output.json"):
            os.remove("output.json")
        files = glob.glob('static/images/*')
        for f in files:
            os.remove(f)

        return jsonify({'message': 'Parapeters set successfully'})

    # if request.method == 'POST':
    #     print("passed condition  submit root")
    #     global searchTerm
    #     global account
    #     account = request.form['account']  # Getting the Input Amazon Product URL
    #     searchTerm = request.form['search_term']
    #
    #     # This will remove any existing file with the same name so that the scrapy will not append the data to any previous file.
    #     if os.path.exists("output.json"):
    #         os.remove("output.json")
    #
    #     return redirect(url_for('scrape'))  # Passing to the Scrape function


@app.route("/scrape")
def scrape():
    # print("hello im in scrape root")
    scrape_with_crochet(account_name=account)  # Passing that URL to our Scraping Function

    # while not scrape_complete:
    while not scrape_complete:
        time.sleep(5)

    # print("size of output data is {}".format(len(output_data)))

    return jsonify(output_data)  # Returns the scraped data after being running for 20 seconds.

    # return render_template("posts.html", posts=output_data)


@app.route("/listen_counter")
def listen_counter():
    def respond_to_client():
        while True:
            time.sleep(10)
            global counter
            counter += 1
            _data = json.dumps({"counter": counter})
            print("counter :{}".format(counter))
            yield f"data: {_data} \n\n"

    return Response(respond_to_client(), mimetype="text/event-stream")


@app.route("/listen_posts")
def listen_posts():
    scrape_with_crochet(account_name=account)

    def get_posts():
        global data_list
        global output_data
        try:
            while not scrape_complete:

                if data_list != output_data:
                    data_list = output_data.copy()
                    _data = json.dumps(output_data)
                    # print(output_data)
                    yield f"data: {_data} \n\n"
                time.sleep(1)
        except GeneratorExit:
            print('closed connection: ')
            close_sse_connection()

        if scrape_complete:
            print("Finished Scraping")
            yield "data: finished\n\n"
            reset_scrape()
            output_data = []

    return Response(get_posts(), mimetype="text/event-stream")


@app.route('/media/<post_id>')
def get_media(post_id):
    filename = f"static/images/{post_id}.jpeg"
    return send_file(filename, mimetype='image/jpeg')


@app.route("/dummy")
def dummy():
    data = [{"mama": "hh"}, {"hoho": 88}]
    return jsonify(data)


@crochet.run_in_reactor
def scrape_with_crochet(account_name):
    # print("im inside scrape with crochet")
    # This will connect to the dispatcher that will kind of loop the code between these two functions.
    dispatcher.connect(_crawler_result, signal=signals.item_scraped)

    # This will connect to the InstaSpider function in our scrapy file and after each yield will pass to the
    # crawler_result function.
    eventual = crawl_runner.crawl(InstagramAccount, usernames=account_name, term=searchTerm,
                                  api_key='32977205-62f6-4698-8045-f940356f090a')

    eventual.addCallback(finished_scrape)

    return eventual


def finished_scrape(null):
    """
    A callback that is fired after the scrape has completed.
    Set a flag to allow display the results from /results
    """
    global scrape_complete
    scrape_complete = True


def reset_scrape():
    """
    A callback that reset the scraping status to resume .
    """
    global scrape_complete
    scrape_complete = False


def close_sse_connection():
    global scrape_complete
    scrape_complete = True
    crawl_runner.stop()


# This will append the data to the output data list.
def _crawler_result(item, response, spider):
    output_data.append(dict(item))


if __name__ == "__main__":
    # app.run(debug=True, port=80)
    http_server = WSGIServer(("localhost", 80), app)
    http_server.serve_forever()
