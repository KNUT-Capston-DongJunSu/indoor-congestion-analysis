import torch
import numpy as np
from ultralytics.data.augment import LetterBox

class PreProcessor(torch.nn.Module):
    def __init__(self, model, imgsz=640, args=None):
        super().__init__()
        self.model = model
        self.imgsz = imgsz
        self.args = args if args is not None else type('Args', (), {'rect': False})()  # 기본 args 객체 생성

    def preprocess(self, im):
            """
            Prepares input image before inference.

            Args:
                im (torch.Tensor | List(np.ndarray)): Images of shape (N, 3, h, w) for tensor, [(h, w, 3) x N] for list.
            """
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            not_tensor = not isinstance(im, torch.Tensor)
            if not_tensor:
                im = np.stack(self.pre_transform(im))
                if im.shape[-1] == 3:
                    im = im[..., ::-1]  # BGR to RGB
                im = im.transpose((0, 3, 1, 2))  # BHWC to BCHW, (n, 3, h, w)
                im = np.ascontiguousarray(im)  # contiguous
                im = torch.from_numpy(im)

            im = im.to(device)
            im = im.half() if self.model.fp16 else im.float()  # uint8 to fp16/32
            if not_tensor:
                im /= 255  # 0 - 255 to 0.0 - 1.0
            return im

    def pre_transform(self, im):
            """
            Pre-transform input image before inference.

            Args:
                im (List[np.ndarray]): Images of shape (N, 3, h, w) for tensor, [(h, w, 3) x N] for list.

            Returns:
                (List[np.ndarray]): A list of transformed images.
            """
            same_shapes = len({x.shape for x in im}) == 1 
            """
            입력 이미지 크기가 모두 같고(same_shapes),
            rect 모드가 활성화돼 있고(self.args.rect),
            모델이 .pt 형식이거나(self.model.pt),
            또는 동적 크기를 지원하고 고정 크기 입력이 아니면(dynamic 이면서 imx가 아님),
            그럴 때 auto=True로 설정해서 LetterBox 같은 전처리 함수가 자동으로 이미지를 네모 형태로 맞추고 최적화한다는 뜻이다.
            """
            letterbox = LetterBox(
                self.imgsz,
                auto=same_shapes
                and self.args.rect # 보통 영상 처리할 때 이미지 크기를 네모난 형태로 맞춰서 처리하겠다는 뜻
                and (self.model.pt or (getattr(self.model, "dynamic", False) and not self.model.imx)),
                stride=self.model.stride,
            )
            return [letterbox(image=x) for x in im]