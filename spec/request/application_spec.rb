# -*- coding: utf-8 -*-
require 'capybara_helper'

describe "Application handle" do

  describe  "request on / and result" do
    before do
      visit '/'
    end
    
    it "has link to user panel" do
      page.has_link?('panel', :href => "/panel").should be_true
    end

    it "has link to registration page" do
      page.has_link?('się zarejestrować', :href => "/register").should be_true
    end
  end

end
