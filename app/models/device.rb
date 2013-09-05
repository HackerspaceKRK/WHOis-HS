class Device
  include DataMapper::Resource

  property :id, Serial
  property :mac, String, :format => /[0-9A-F]{2}(\:[0-9A-F]{2}){5}/
  property :last_seen, DateTime 

  belongs_to :user
end

