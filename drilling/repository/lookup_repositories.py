from drilling.repository.generic_repository import GenericRepository


class PhaseRepository(GenericRepository):
   
    def __init__(self, db):
        super().__init__(db, collection_name="phases")


class CategoryRepository(GenericRepository):
    
    def __init__(self, db):
        super().__init__(db, collection_name="categories")


class ResponsiblePartyRepository(GenericRepository):
   
    def __init__(self, db):
        super().__init__(db, collection_name="responsibleParties")


class WellRepository(GenericRepository):
    
    def __init__(self, db):
        super().__init__(db, collection_name="wells")