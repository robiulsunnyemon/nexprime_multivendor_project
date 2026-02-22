from app.database.db import prisma
from app.core.upload_img_helper import upload_image_helper
from fastapi import UploadFile, HTTPException, status
from typing import Optional, Union

class CategoryService:
    @staticmethod
    async def get_all_main_categories():
        main_categories = await prisma.maincategory.find_many(
            include={
                "subCategories": {
                    "include": {
                        "products": True
                    }
                }
            },
            order={"name": "asc"}
        )
        
        # Convert to list of dicts to add 'product_count' without Pydantic validation errors
        results = []
        for main_cat in main_categories:
            main_cat_dict = main_cat.model_dump()
            if main_cat.subCategories:
                main_cat_dict["subCategories"] = []
                for sub_cat in main_cat.subCategories:
                    sub_cat_dict = sub_cat.model_dump()
                    sub_cat_dict["products"] = [p.model_dump() for p in sub_cat.products] if sub_cat.products else []
                    sub_cat_dict["product_count"] = len(sub_cat_dict["products"])
                    main_cat_dict["subCategories"].append(sub_cat_dict)
            results.append(main_cat_dict)
                    
        return results

    @staticmethod
    async def get_subcategory_details(subcategory_id: int):
        sub_cat = await prisma.subcategory.find_unique(
            where={"id": subcategory_id},
            include={
                "products": True
            }
        )
        if not sub_cat:
            raise HTTPException(status_code=404, detail="Sub-category not found")
            
        sub_cat_dict = sub_cat.model_dump()
        sub_cat_dict["products"] = [p.model_dump() for p in sub_cat.products] if sub_cat.products else []
        sub_cat_dict["product_count"] = len(sub_cat_dict["products"])
        return sub_cat_dict

    @staticmethod
    async def get_subcategories_by_main(identifier: Union[int, str]):
        if isinstance(identifier, int) or identifier.isdigit():
            main_cat_id = int(identifier)
            return await prisma.subcategory.find_many(
                where={"mainCategoryId": main_cat_id},
                order={"name": "asc"}
            )
        else:
            main_cat = await prisma.maincategory.find_unique(where={"name": identifier})
            if not main_cat:
                raise HTTPException(status_code=404, detail="Main category not found")
            return await prisma.subcategory.find_many(
                where={"mainCategoryId": main_cat.id},
                order={"name": "asc"}
            )

    @staticmethod
    async def create_subcategory(name: str, main_category_id: int, image_file: Optional[UploadFile] = None):
        image_url = None
        if image_file:
            image_url = await upload_image_helper(image_file, folder="nexprime_categories")
        
        return await prisma.subcategory.create(
            data={
                "name": name,
                "mainCategoryId": main_category_id,
                "image": image_url
            }
        )

    @staticmethod
    async def delete_subcategory(subcategory_id: int):
        sub_cat = await prisma.subcategory.find_unique(where={"id": subcategory_id})
        if not sub_cat:
            raise HTTPException(status_code=404, detail="Sub-category not found")
        return await prisma.subcategory.delete(where={"id": subcategory_id})
