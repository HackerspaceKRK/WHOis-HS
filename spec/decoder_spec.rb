require 'spec_helper'

describe Decoder do
  let(:aes) do
    aes = OpenSSL::Cipher::AES.new(Whois::Encryption.block_size,Whois::Encryption.method)
    aes.encrypt
  end
  let(:key) { aes.random_key }
  let(:iv) { aes.random_iv }
  
  let(:message) { "ala ma kota" }

  let(:decoder) { Decoder.new(key) }

  def encode(message)
    return iv + aes.update(message) + aes.final
  end

  it "decode message corectly" do
    decoder.decode(encode(message)).should == message
  end
end
