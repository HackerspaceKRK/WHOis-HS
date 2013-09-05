class User
  include DataMapper::Resource

  property :id, Serial


  property :display_name, String, :length => 100, :required => true

  property :login, String, :required => true , :length => 10
  


end
