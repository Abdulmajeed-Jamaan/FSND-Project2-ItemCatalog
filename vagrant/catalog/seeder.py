#!/usr/bin/env python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item, User

engine = create_engine('sqlite:///Category_item.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="tempUser", email="tempUser@udacity.com",
             picture='''https://pbs.twimg.com/profile_images/2671170543
             /18debd694829ed78203a5a36dd364160_400x400.png''')
session.add(User1)
session.commit()

# Menu for UrbanBurger
category1 = Category(user_id=1, title="Soccer")
session.add(category1)
session.commit()


Item1 = Item(user_id=1, title="Ball",  category=category1,
             description="ball for playing with wooho!")
session.add(Item1)
session.commit()

Item2 = Item(user_id=1, title="Choose",  category=category1,
             description="choose to weare them before playing ")
session.add(Item2)
session.commit()

Item3 = Item(user_id=1, title="flag",  category=category1,
             description="flag for rise up when you are in match")
session.add(Item3)
session.commit()

# Menu for UrbanBurger
category2 = Category(user_id=1, title="Skating")
session.add(category2)
session.commit()


Item4 = Item(user_id=1, title="Board",  category=category2,
             description="to use it when skating")
session.add(Item4)
session.commit()

Item5 = Item(user_id=1, title="Gloves",  category=category2,
             description="to protect you hand")
session.add(Item5)
session.commit()

Item6 = Item(user_id=1, title="Helmet",  category=category2,
             description="to protect you head when you fall ")
session.add(Item6)
session.commit()


# Menu for UrbanBurger
category3 = Category(user_id=1, title="Baseball")
session.add(category3)
session.commit()


Item7 = Item(user_id=1, title="Paddle",  category=category3,
             description="to throw the ball")
session.add(Item7)
session.commit()

Item8 = Item(user_id=1, title="T-shirt",  category=category3,
             description="for you favorite team")
session.add(Item8)
session.commit()

Item9 = Item(user_id=1, title="Chest Armor",  category=category3,
             description="to protect your cheast from powerfull throws")
session.add(Item9)
session.commit()


print "added catalog items!"
