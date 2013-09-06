

class Decoder

  IV_LENGTH = Whois::Encryption.block_size/8
  
  def initialize(key)
    @aes = OpenSSL::Cipher::AES.new(Whois::Encryption.block_size,Whois::Encryption.method)
    @aes.decrypt
    @aes.key = key
  end

  def decode(message)
    @aes.iv = message[0,IV_LENGTH]
    data = message[IV_LENGTH,message.length]
    return (@aes.update(data) + @aes.final)
  end
end
