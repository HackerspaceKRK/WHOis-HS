require 'net/http'

class UpstreamProvider
  def initialize(uri,agent = Net::Http,decoder = Decoder.new)
    @agent = agent
    @uri = uri
    @decoder = decoder
  end

  def fetch_data
    @result = @agent.get(@uri)
    @data = @decoder.decode(@result)
  end

  def active_users
    []
  end
end
