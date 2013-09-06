module Whois
  class Application < Sinatra::Base
    
    get '/' do
      erb :index
    end

    get '/whois' do
      content_type 'application/json'
    end

  end
end
