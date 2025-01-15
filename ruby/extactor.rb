require 'base64'
require 'json'
require 'selenium-webdriver'
require 'time'
require 'pathname'
require 'yaml'

class CorrectAnswerNotFoundError < StandardError; end

# Load configuration from YAML file
config_file = '/home/rgomez/RubymineProjects/Obtain-Test-Answers/ruby/config/config.yml'
config = YAML.safe_load(File.read(config_file))

# Extract configuration values
driver_path = config['path']['driver']
answers_file_path = config['path']['answers-file-rute']
page_url = config['url']['page-url']

class WebScraping
  def initialize(config)
    @config = config # Guardamos config como una variable de instancia

    # Configure Firefox options based on config
    @options = Selenium::WebDriver::Firefox::Options.new
    @options.add_argument('--headless') if @config['headless']  # Usamos @config para acceder al valor

    # Initialize WebDriver using driver path from config
    @service = Selenium::WebDriver::Service.firefox(path: @config['path']['driver'])
    @driver = Selenium::WebDriver.for :firefox, options: @options, service: @service
  end

  def load_page(url)
    @driver.navigate.to(url)
  end

  def find_element(by, value)
    @driver.find_element(by, value)
  rescue Selenium::WebDriver::Error::NoSuchElementError
    raise CorrectAnswerNotFoundError, "Element not found on page"
  end
end

# Create scraper instance and load the page URL from config
scraper = WebScraping.new(config)
scraper.load_page(page_url)
