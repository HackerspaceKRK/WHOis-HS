class User
  include DataMapper::Resource

  property :id, Serial


  property :display_name, String, :length => 100
end
