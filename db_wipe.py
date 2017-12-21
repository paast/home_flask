from main import db, User, Node, Link


def run():
	db.session.query(Link).delete()
	db.session.query(Node).delete()
	db.session.query(User).delete()
	db.session.commit()

if __name__ == "__main__":
	run()