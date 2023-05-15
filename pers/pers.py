from typing import Any, Callable, List
from ncache import Cache

class PersistentResults:
    def __init__(self, 
        filename:str, 
        tmpfilename:str=None, 
        interval:int=1, 
        load:bool=True,               # if False the results will be replaced
        exeption_on_duplicate:bool=False,
        arg_prefix:str='_arg_',       # prefix for positional arguments (by default '_arg_': _arg_0, _arg_1, ..., _arg_n)
        result_key:str='result',      # key of the result if not flatten_result
        flatten_result:bool=True,     # flatten the results - return 2D table
        result_prefix:str='_result_', # prefix of result entries if flatten_result
    ):
        self.load           = load
        self.interval       = interval
        self.flatten_result = flatten_result
        self.arg_prefix     = arg_prefix
        self.result_prefix  = result_prefix
        self.result_key     = result_key
        self.exeption_on_duplicate = exeption_on_duplicate

        self.results = Cache(filename, tmpfilename=tmpfilename)
        self.counter = 0
        
        if self.load:
            self.results.load_cache()
    
    class ResultAlreadyExistsException(Exception):
        pass

    @property
    def filename(self)->str:
        return self.results.cache_filename

    @property
    def data(self)->List[dict]:
        return list(self.results.data.values())

    def _flatten_result(self, res:Any)->dict:
        # print('_flatten_result:res', res)
        if isinstance(res, dict):
            return {f'{self.result_prefix}{k}':v for k,v in res.items()}
        elif isinstance(res, (list, tuple)):
            return {f'{self.result_prefix}{idx}':x for idx, x in enumerate(res)}
        else:
            return {self.result_key: res}


    def append(self, fun:Callable, *args:Any, **kwargs:Any)->dict:
        try:
            _hash = self.results.get_hash([args, kwargs]) 
            val = self.results.get_value(_hash)  # raise NoCacheValue exception if not found
            if self.exeption_on_duplicate:
                raise self.ResultAlreadyExistsException(f'Element already exists for: {args}, {kwargs}')
            return val
        except Cache.NoCacheValue:
            res = fun(*args, **kwargs)
            if self.flatten_result:
                res = self._flatten_result(res)
                # jeżeli w wyniku zostaly zwrocone argumenty funkcji to zignoruj te z identycznymi wartosciami
                kwargs2 = {}
                for k, v in kwargs.items():
                    if k in res:
                        if v != res[k]:
                            # TODO: poprawic komunikat
                            raise Exception(f'Conflict!\nThere is argument with key {k}:{v} which is different than result with the same name {k}:{res[k]}\nYou can change the prefix or turn off flatten result')
            else:
                res = {self.result_key: res}


            val = {
                **res,
                **{f'{self.arg_prefix}{idx}':x for idx, x in enumerate(args)},
                **kwargs,
            }
            self.results.set_value(_hash, val)
            self.counter += 1
            if self.counter % self.interval == 0:
                self.results.save_cache()
            return val

    def __getitem__(self, item:int)->dict:
        return self.data[item]

    def __getslice__(self, start:int, stop:int)->List[dict]:
        return self.data[start:stop]

    def __len__(self)->int:
        return len(self.data)

    def save(self):
        self.results.save_cache()
        
