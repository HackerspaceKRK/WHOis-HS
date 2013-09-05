module Whois
  ROOT = Dir.pwd

  def self.root 
    ROOT
  end
  
  def self.db_url
    "sqlite://#{Whois.root}/db/database.sqlite"
  end
end
