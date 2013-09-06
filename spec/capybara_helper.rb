require_relative 'spec_helper.rb'

require 'capybara/rspec'

Capybara.app = Whois::Application

RSpec.configure do |config|
  config.include(Capybara::DSL)
end
