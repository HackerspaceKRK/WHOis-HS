require 'digest'

class User
  include DataMapper::Resource

  property :id, Serial
  property :display_name, String, :length => 100, :required => true
  property :login, String, :required => true , :length => 10
  property :last_login, Date 
  property :password, String, :length => 64, :writer => :private

  has n, :device

  def password=(new_password)
    super(hash_password(new_password))
  end

  def authenticate(password)
    return self.password == hash_password(password)
  end

  private

  def hash_password(password)
    Digest::SHA2.hexdigest(password)
  end
end
