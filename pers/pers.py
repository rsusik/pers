from typing import Any, Callable, List, Tuple
from itertools import product
import inspect
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
        skip_list:list[str]=None,     # list of arguments and results that shouldn't be added to results
    ):
        self.load           = load
        self.interval       = interval
        self.flatten_result = flatten_result
        self.arg_prefix     = arg_prefix
        self.result_prefix  = result_prefix
        self.result_key     = result_key
        self.exeption_on_duplicate = exeption_on_duplicate
        if skip_list is not None:
            self.skip_list = skip_list
        else:
            self.skip_list = []

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
        if isinstance(res, dict):
            return {f'{self.result_prefix}{k}':v for k,v in res.items()}
        elif isinstance(res, (list, tuple)):
            return {f'{self.result_prefix}{idx}':x for idx, x in enumerate(res)}
        else:
            return {self.result_key: res}


    def _get_args_kwargs_hash(self, el, args, kwargs):
        _args = el[:len(args)]
        _kwargs = dict(zip(kwargs.keys(), el[len(args):]))
        _hash = self.results.get_hash([_args, _kwargs])
        return _args, _kwargs, _hash


    def all(self, *args:List, **kwargs:List)->bool:
        '''
        Returns True if results contain all records for
        product of given arguments and False otherwise
        '''
        l = product(*args, *kwargs.values())
        for el in l:
            _, _, _hash = self._get_args_kwargs_hash(el, args, kwargs)
            try:
                _ = self.results.get_value(_hash)
            except Cache.NoCacheValue:
                return False
        return True


    def any(self, *args:List, **kwargs:List)->bool:
        '''
        Returns True if any results contain any records 
        from product of given arguments and False otherwise
        '''
        l = product(*args, *kwargs.values())
        for el in l:
            _, _, _hash = self._get_args_kwargs_hash(el, args, kwargs)
            try:
                _ = self.results.get_value(_hash)
            except Cache.NoCacheValue:
                continue
            return True
        return False


    def missing(self, *args:List, **kwargs:List)->List[Tuple[list, dict]]:
        '''
        Returns all missing records for product of given arguments
        '''
        l = product(*args, *kwargs.values())
        missing = []
        for el in l:
            _args, _kwargs, _hash = self._get_args_kwargs_hash(el, args, kwargs)
            try:
                _ = self.results.get_value(_hash)
            except Cache.NoCacheValue:
                missing.append((_args, _kwargs))
        return missing


    def append(self, fun:Callable, *args:Any, **kwargs:Any)->dict:
        '''
        Appends new result of function `fun` for given arguments
        if it does not exists already and returns the value.
        The function checks if a record with given arguments already
        exists, if not then it executes function `fun` with given arguments
        and returns the result.
        Otherwise, returns the existing value.
        '''
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
                for k, v in kwargs.items():
                    if k in res:
                        if v != res[k]:
                            # TODO: poprawic komunikat
                            raise Exception(f'Conflict!\nThere is argument with key {k}:{v} which is different than result with the same name {k}:{res[k]}\nYou can change the prefix or turn off flattening result')
            else:
                res = {self.result_key: res}

            arg_names = list(inspect.signature(fun).parameters.keys())
            args_dict = {arg_names[idx]: el for idx, el in enumerate(args)}
            all_args = {**args_dict, **kwargs, **res}

            val = {
                # **res,
                # **{f'{self.arg_prefix}{idx}':x for idx, x in enumerate(args)},
                # **kwargs,
                **{k:v for k, v in all_args.items() if k not in self.skip_list}
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
        
