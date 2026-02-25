from database import SessionLocal
from inventory import Site, Asset

# فتح جلسة قاعدة البيانات
db = SessionLocal()

try:
    # --- إضافة Sites وهمية مع التحقق من التكرار ---
    sites_data = [
        {"name": "Main Warehouse", "location": "Cairo"},
        {"name": "Secondary Storage", "location": "Alexandria"},
        {"name": "Remote Depot", "location": "Giza"}
    ]

    site_objects = []
    for s in sites_data:
        # تحقق قبل الإضافة إن الـ site مش موجود بالفعل
        existing_site = db.query(Site).filter(Site.name == s["name"]).first()
        if existing_site:
            site_objects.append(existing_site)  # لو موجود بالفعل استخدمه
            continue
        site = Site(name=s["name"], location=s["location"])
        db.add(site)
        db.flush()  # لإعطاء id قبل الـ commit
        site_objects.append(site)

    db.commit()  # حفظ الـ Sites
    for site in site_objects:
        db.refresh(site)

    # --- إضافة Assets وهمية مع التحقق من التكرار ---
    assets_data = [
        {"name": "Laptop Dell XPS", "category": "Electronics", "site_id": site_objects[0].id},
        {"name": "Printer HP LaserJet", "category": "Electronics", "site_id": site_objects[0].id},
        {"name": "Office Chair", "category": "Furniture", "site_id": site_objects[1].id},
        {"name": "Projector Epson", "category": "Electronics", "site_id": site_objects[2].id},
        {"name": "Whiteboard", "category": "Furniture", "site_id": site_objects[2].id}
    ]

    for a in assets_data:
        # تحقق قبل الإضافة إن الـ asset مش موجود بالفعل بنفس الاسم ونفس الموقع
        existing_asset = db.query(Asset).filter(
            Asset.name == a["name"],
            Asset.site_id == a["site_id"]
        ).first()
        if existing_asset:
            continue
        asset = Asset(name=a["name"], category=a["category"], site_id=a["site_id"])
        db.add(asset)

    db.commit()
    print("✅ Database populated with sample Sites and Assets safely!")

except Exception as e:
    db.rollback()
    print("Error:", e)
finally:
    db.close()