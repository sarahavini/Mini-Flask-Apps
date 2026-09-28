#to run, in terminal #python -V +enter, python .\seed.py +enter

from app import app, db, ToolsLibrary, Users

with app.app_context():
    print("DB:", app.config["SQLALCHEMY_DATABASE_URI"])
    #with db.engine.begin() as conn:
       # conn.exec_driver_sql(
       #     "ALTER TABLE tools_library ADD COLUMN checked_out_to INTEGER REFERENCES users(id)"
        #)
    #print("column added")

    def get_or_create_user(name, email=None):
        user = Users.query.filter_by(user_name=name).first()
        if user is None:
            user = Users(
                user_name=name,
                email=email or f"{name.lower()}@example.com",
                password_hash="changeme",
            )
            db.session.add(user)
            db.session.flush()  # assigns user.id
        return user

    sarah = get_or_create_user("Sarah")
    sprinkles = get_or_create_user("Sprinkles")
    db.session.commit()

    # wipe tools only
    ToolsLibrary.query.delete()
    db.session.commit()

    db.session.add_all([
        ToolsLibrary(
            tool_name="Weed Whacker",
            tool_description="Whacks Weeds",
            tool_condition="Brand New",
            tool_available=True,
            owner_id=sarah.id,
            checked_out_to=None,
        ),
        ToolsLibrary(
            tool_name="lawn mower",
            tool_description="mows lawns and weeds",
            tool_condition="really old",
            tool_available=True,
            owner_id=sarah.id,
            checked_out_to=None,
        ),
        ToolsLibrary(
            tool_name="Screw Driver",
            tool_description="Screws Stuff",
            tool_condition="Meh",
            tool_available=False,
            owner_id=sprinkles.id,
            checked_out_to=sarah.id,  # example checkout
        ),
    ])
    db.session.commit()

    print("tools", ToolsLibrary.query.count(), "users", Users.query.count())
    for t in ToolsLibrary.query.all():
        print(t.id, t.tool_name, "owner", t.owner_id, "out to", t.checked_out_to)