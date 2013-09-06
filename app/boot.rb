require 'bundler/setup'
Bundler.require

Dir.chdir('app') do
  Dir['providers/**.rb'].each do |provider|
    require_relative provider
  end
end

require_relative 'config.rb'
require_relative 'db.rb'
require_relative 'decoder.rb'
require_relative 'application.rb'
