require 'spec_helper'

describe UpstreamProvider do
  
  let(:uri) { "http://whois.hskrk.pl/" }
  let(:agent) { fake(Net::HTTP) }
  let(:decoder) { fake(Decoder) }
  let(:provider) { UpstreamProvider.new(uri,agent,decoder) }

  subject { provider }

  it { should respond_to(:active_users) }
  
  it 'make request to specyfied URL' do
    provider.fetch_data
    agent.should have_received.get(uri)
  end

  it 'encrypt data from request' do
    data = 'ala ma kota'
    stub(agent).get(uri) { data }
    provider.fetch_data
    decoder.should have_received.decode(data)
  end
  
end
