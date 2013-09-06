class Activity
  include DataMapper::Resource

  property :id, Serial
  property :form, DateTime
  property :to, DateTime

  belongs_to :user
end
