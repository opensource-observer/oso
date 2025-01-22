{{
  config(
    materialized='table',
    meta={
      'sync_to_db': False
    }
  )
}}

with address_list as (
  select address from unnest([
    '0x5c8c76f2e990f194462dc5f8a8c76ba16966ed42',
    '0x5a7facb970d094b6c7ff1df0ea68d99e6e73cbff',
    '0xd0f92f5d756bf223574dfa3ef284a35c3c046289',
    '0x0c5527b3abfbd0c297104b12be6f288d335b299c',
    '0x87eee96d50fb761ad85b1c982d28a042169d61b1',
    '0x73a7fe27fe9545d53924e529acf11f3073841b9e',
    '0xe48b4e392e4fc29ac2600c3c8efe0404a15d60d9',
    '0xe7910f8a4b7efcf2964f017e34e4e2d9aa06edc3',
    '0x00000000fc04c910a0b5fea33b03e0447ad0b0aa',
    '0xa41214012d4462ecbb0724673897ee0dcc0fdf49',
    '0x5d40015034da6cd75411c54dd826135f725c2498',
    '0xdbdfd5b04fc3a19c40f2b12f6ca29bd772ccb822',
    '0x2416092f143378750bb29b79ed961ab195cceea5',
    '0xbf5495efe5db9ce00f80364c8b423567e58d2110',
    '0x14e09a1a78950b38ab3b203cdaa0fcb331b9ee26',
    '0x5f451da1b3ad7bf2845573fcca2808d75065a6f4',
    '0xc0ddbaaeed6fc3e2f4f4efa5778383b0e356621e',
    '0x50c28a42ac91f6e6437a036d320c9242432cce3f',
    '0x9eb516290582424b603e76d66b55d0b268880ed1',
    '0xb35659cbac913d5e4119f2af47fd490a45e2c826',
    '0xb251b4a49de4da1ef8758f78c02678e762388fc0',
    '0xd6b270dfee268b452c86251fd7e12db8de9200fb',
    '0xcb54808f5ef6fd88b933c55dd4f4c365e61828bb',
    '0x1bcbb33ff4272c4fe3a00eaa7958953037a3a471',
    '0xa1dabef33b3b82c7814b6d82a79e50f4ac44102b',
    '0x6e3fddab68bf1ebaf9dacf9f7907c7bc0951d1dc',
    '0x70843ce8e54d2b87ee02b1911c06ea5632cd07d3',
    '0xb04a484387a7242339da615a63d2d49d8968aada',
    '0xe0bec4f45aef64cec9dcb9010d4beffb13e91466',
    '0xf9cfb8a62f50e10adde5aa888b44cf01c5957055',
    '0xbb505c54d71e9e599cb8435b4f0ceec05fc71cbd',
    '0x5f8d42635a2fa74d03b5f91c825de6f44c443da5',
    '0x79a5a9e97dc8f4a1c2370e1049db960275431793',
    '0x01ef58e98e389ff5fb80a7b00e495b81cb6298d9',
    '0x5dc1a8fa98508e342fa8cff0c49ab57138d53337',
    '0x2d13ac7ad45fd3b0d146c8c9e508aa0443123525',
    '0x524fe171e80173c15381bb50034033da282abcc6',
    '0x588f26d5befe74dc61694a7b36227c0e0c52c0f9',
    '0xe807f3282f3391d237ba8b9becb0d8ea3ba23777',
    '0xd68e7d20008a223dd48a6076aaf5edd4fe80a899',
    '0xbded651c03e2bc332aa49c1ffca391eaa3ea6b86',
    '0xdcb421cc4cbb7267f3b2cacab44ec18aebed6724',
    '0x0df840dcbf1229262a4125c1fc559bd338ec9491',
    '0xd4c00fe7657791c2a43025de483f05e49a5f76a6',
    '0xb6b9e9e56ab5a4af927faa802ac93786352f3af9',
    '0x4aba01fb8e1f6bfe80c56deb367f19f35df0f4ae',
    '0xc55e93c62874d8100dbd2dfe307edc1036ad5434',
    '0xa25c582874f984dd58f729ef970922a3691a1c69',
    '0x0ad86842eadee5b484e31db60716eb6867b46e21',
    '0xe945d527de9c5121eda9cf48e23cdf691894d4c0',
    '0xde5990625c5b70b6af6d6991f17abfc8c27acc72',
    '0xbe7946b7988a6556cfb78258592350e706786d36',
    '0xde79e22b1b0b02cdbff3325bfb62dbcf1e65ca19',
    '0xe40714459d9493994be025f04afc38d2bcf42f8e',
    '0x579a18207242c250addb67cc4d49f34a5f659449',
    '0x93326d53d1e8ebf0af1ff1b233c46c67c96e4d8d',
    '0x6a189e0e8d3b6b0455dc49e81cc0df33904af9e8',
    '0x17a7f6a839fea3b716b43f9414ffc93131878bd2',
    '0x3ef3d8ba38ebe18db133cec108f4d14ce00dd9ae',
    '0x3b5a0fc12f8fd8b26d251f28258d1d172f930f8a',
    '0xc78d4395f6ed4e7037faffe634b7b3f8af376a8d',
    '0x1026d3d219098d7b1b0a180f7e557deea7da82c1',
    '0x61ffe014ba17989e743c5f6cb21bf9697530b21e',
    '0xee6a57ec80ea46401049e92587e52f5ec1c24785',
    '0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad',
    '0x42b24a95702b9986e82d421cc3568932790a48ec',
    '0x54df9e11c7933a9ca3bd1e540b63da15edae40bf',
    '0x91ae842a5ffd8d12023116943e72a606179294f3',
    '0xb753548f6e010e7e680ba186f9ca1bdab2e90cf2',
    '0x000000000022d473030f116ddee9f6b43ac78ba3',
    '0xa5644e29708357803b5a882d272c41cc0df92b34',
    '0x1f98431c8ad98523631ae4a59f267346ea31f984',
    '0xc36442b4a4522e871399cd717abdd847ab11fe88',
    '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45',
    '0xe34139463ba50bd61336e0c446bd8c0867c6fe65',
    '0xbfd8137f7d1516d3ea5ca83523914859ec47f573',
    '0x93d2118bdd8b5e243020f01a1391b2e3cb137a56',
    '0xfdbb4d606c199f091143bd604c85c191a526fbd0',
    '0xea173648f959790baea225ce3e75df8a53a6bde5',
    '0xd152f549545093347a162dce210e7293f1452150',
    '0xf89e24bad60d78386a5fe6b6c897dd4d88a9ed70',
    '0xbc404429558292ee2d769e57d57d6e74bbd2792d',
    '0xc1ab11375aadd9463036d6fa894ed905e1fbb65a',
    '0x8cca517370cbfc33cc9810bfc7440832c47d251c',
    '0xe04bb5b4de60fa2fba69a93ade13a8b3b569d5b4',
    '0x343910697c03477e5cc0d386ffa5133d1a827ad7',
    '0xc224bf25dcc99236f00843c7d8c4194abe8aa94a',
    '0xdc1f5b81eec7e6391aeb6c8e5a2000d3a9aa8e6d',
    '0x595d607a5ef39a0a2016d785e60df74afbc78cc6',
    '0x9fa8ca2013620263a68919fc18b0667f21ddb76e',
    '0x9bffe86ba69f7d91ae67f70896aee42698e2d3db',
    '0x0bfa5a013dbd0791f0f8171afbab45edaa372dbf',
    '0x81476ceae27466572bea9b3397f0eab4a02f6792',
    '0x3835b46bb20c056a48a53e6c892811fbcc43862e',
    '0x2c5048218b414c7d1e1d590b9f0738cf7349fea7',
    '0x6c7d7714f536cbdb0b3b0fddea2747d5c4b2668e',
    '0x8250f4af4b972684f7b336503e2d6dfedeb1487a',
    '0xa2aa501b19aff244d90cc15a4cf739d2725b5729',
    '0xff1a0f4744e8582df1ae09d5611b887b6a12925c',
    '0xff0375667570d0e6572360e9dfbe8f2a6d85ae87',
    '0x59f78de21a0b05d96ae00c547ba951a3b905602f',
    '0x5cc070844e98f4cec5f2fbe1592fb1ed73ab7b48',
    '0x9d89bca142498fe047bd3e169de8ed028afab07f',
    '0xd6e27844a260998fa5ccd9908b63488eb73198f8',
    '0x5a973117dd273676bf4d14313b80562dc8973ba9',
    '0x16779885375d32e7327fade91f91b5a722bb5cf4'
  ]) as address
)

select
  dt,
  block_timestamp,
  from_address,
  to_address,
  chain,
  value_64
from {{ source('optimism_superchain_raw_onchain_data', 'transactions') }}
where
  dt >= '2024-06-01'
  and receipt_status = 1
  and (
    to_address in (select address from address_list)
    or from_address in (select address from address_list)
  )